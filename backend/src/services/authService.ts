import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import crypto from "crypto";
import { cacheGet, cacheSet, cacheDel } from "./redis";
import * as dbService from "./dbService";
import { sendVerificationEmail } from "./emailService";
import { AuthPayload } from "../types";

const REFRESH_TTL        = 30 * 24 * 60 * 60; // 30 days
const VERIFY_TTL         = 24 * 60 * 60;       // 24 hours
const RESEND_COOLDOWN    = 60;                  // 60 seconds between resends
const BCRYPT_ROUNDS      = 12;

function getSecret(): string {
  const secret = process.env.JWT_SECRET;
  if (!secret) throw new Error("JWT_SECRET not configured");
  return secret;
}

function issueTokens(userId: string, email: string) {
  const secret = getSecret();
  const accessToken = jwt.sign(
    { userId, email },
    secret,
    { expiresIn: (process.env.JWT_EXPIRES_IN || "7d") as jwt.SignOptions["expiresIn"] }
  );
  const refreshToken = jwt.sign(
    { userId, email },
    secret,
    { expiresIn: (process.env.JWT_REFRESH_EXPIRES_IN || "30d") as jwt.SignOptions["expiresIn"] }
  );
  return { accessToken, refreshToken };
}

// ---------------------------------------------------------------------------

export interface RegisterInput {
  email: string;
  password: string;
  name?: string;
}

export interface RegisterResult {
  message: string;
}

export async function register(input: RegisterInput): Promise<RegisterResult> {
  const { email, password, name } = input;
  console.log(`[authService] register → email=${email}`);

  if (!email || !password) throw new Error("email and password are required");

  const existing = await dbService.findUserByEmail(email);
  if (existing) throw new Error("Email already registered");

  const passwordHash = await bcrypt.hash(password, BCRYPT_ROUNDS);
  const user = await dbService.createUser({ email, name, passwordHash });
  console.log(`[authService] register — user created id=${user.id}`);

  // Generate a secure random token, store in Redis for 24h
  const token = crypto.randomBytes(32).toString("hex");
  await cacheSet(`verify:${token}`, user.id, VERIFY_TTL);

  await sendVerificationEmail(email, token);
  console.log(`[authService] register — verification email sent to ${email}`);

  return { message: "Check your email to verify your account" };
}

// ---------------------------------------------------------------------------

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthResult {
  userId: string;
  email: string;
  name?: string;
  accessToken: string;
  refreshToken: string;
}

export async function login(input: LoginInput): Promise<AuthResult> {
  const { email, password } = input;

  if (!email || !password) throw new Error("email and password are required");

  const user = await dbService.findUserByEmail(email);
  if (!user) throw new Error("Invalid credentials");

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) throw new Error("Invalid credentials");

  if (!user.isVerified) throw new Error("Email not verified");

  const { accessToken, refreshToken } = issueTokens(user.id, email);
  await cacheSet(`refresh:${user.id}`, refreshToken, REFRESH_TTL);

  return { userId: user.id, email, name: user.name ?? undefined, accessToken, refreshToken };
}

// ---------------------------------------------------------------------------

export async function verifyEmail(token: string): Promise<void> {
  const userId = await cacheGet<string>(`verify:${token}`);
  if (!userId) throw new Error("Verification link is invalid or has expired");

  await dbService.markUserVerified(userId);
  await cacheDel(`verify:${token}`);
  console.log(`[authService] verifyEmail — userId=${userId} verified`);
}

// ---------------------------------------------------------------------------

export async function resendVerification(email: string): Promise<void> {
  const user = await dbService.findUserByEmail(email);
  if (!user) return; // Don't reveal whether email exists

  if (user.isVerified) throw new Error("Email is already verified");

  // Rate-limit: one resend per 60 seconds per user
  const cooldownKey = `resend:${user.id}`;
  const onCooldown = await cacheGet<string>(cooldownKey);
  if (onCooldown) throw new Error("Please wait before requesting another email");

  const token = crypto.randomBytes(32).toString("hex");
  await cacheSet(`verify:${token}`, user.id, VERIFY_TTL);
  await cacheSet(cooldownKey, "1", RESEND_COOLDOWN);

  await sendVerificationEmail(email, token);
  console.log(`[authService] resendVerification — email sent to ${email}`);
}

// ---------------------------------------------------------------------------

export interface RefreshResult {
  accessToken: string;
  refreshToken: string;
}

export async function refreshTokens(token: string): Promise<RefreshResult> {
  const payload = jwt.verify(token, getSecret()) as AuthPayload;

  const stored = await cacheGet<string>(`refresh:${payload.userId}`);
  if (!stored || stored !== token) throw new Error("Refresh token invalid or revoked");

  const { accessToken, refreshToken } = issueTokens(payload.userId, payload.email);
  await cacheSet(`refresh:${payload.userId}`, refreshToken, REFRESH_TTL);

  return { accessToken, refreshToken };
}

export async function refreshByUserId(userId: string): Promise<string> {
  const stored = await cacheGet<string>(`refresh:${userId}`);
  if (!stored) throw new Error("Session expired or not found");

  const payload = jwt.verify(stored, getSecret()) as AuthPayload;
  const { accessToken, refreshToken } = issueTokens(payload.userId, payload.email);
  await cacheSet(`refresh:${userId}`, refreshToken, REFRESH_TTL);

  return accessToken;
}

// ---------------------------------------------------------------------------

export async function logout(userId: string): Promise<void> {
  await cacheDel(`refresh:${userId}`);
}

export function verifyAccessToken(token: string): AuthPayload {
  return jwt.verify(token, getSecret()) as AuthPayload;
}
