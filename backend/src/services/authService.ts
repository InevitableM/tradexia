import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { cacheGet, cacheSet, cacheDel } from "./redis";
import * as dbService from "./dbService";
import { AuthPayload } from "../types";

const REFRESH_TTL = 30 * 24 * 60 * 60; // 30 days in seconds
const BCRYPT_ROUNDS = 12;

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

export interface AuthResult {
  userId: string;
  email: string;
  name?: string;
  accessToken: string;
  refreshToken: string;
}

export async function register(input: RegisterInput): Promise<AuthResult> {
  const { email, password, name } = input;
  console.log(`[authService] register → email=${email}`);

  if (!email || !password) throw new Error("email and password are required");

  const existing = await dbService.findUserByEmail(email);
  if (existing) throw new Error("Email already registered");

  const passwordHash = await bcrypt.hash(password, BCRYPT_ROUNDS);
  console.log(`[authService] register — password hashed`);

  const user = await dbService.createUser({ email, name, passwordHash });
  console.log(`[authService] register — user created id=${user.id}`);

  const { accessToken, refreshToken } = issueTokens(user.id, email);
  await cacheSet(`refresh:${user.id}`, refreshToken, REFRESH_TTL);
  console.log(`[authService] register — tokens issued, refresh stored in Redis`);

  return { userId: user.id, email, name, accessToken, refreshToken };
}

// ---------------------------------------------------------------------------

export interface LoginInput {
  email: string;
  password: string;
}

export async function login(input: LoginInput): Promise<AuthResult> {
  const { email, password } = input;

  if (!email || !password) throw new Error("email and password are required");

  const user = await dbService.findUserByEmail(email);
  if (!user) throw new Error("Invalid credentials");

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) throw new Error("Invalid credentials");

  const { accessToken, refreshToken } = issueTokens(user.id, email);
  await cacheSet(`refresh:${user.id}`, refreshToken, REFRESH_TTL);

  return { userId: user.id, email, name: user.name ?? undefined, accessToken, refreshToken };
}

// ---------------------------------------------------------------------------

export interface RefreshResult {
  accessToken: string;
  refreshToken: string;
}

export async function refreshTokens(token: string): Promise<RefreshResult> {
  const payload = jwt.verify(token, getSecret()) as AuthPayload;

  const stored = await cacheGet<string>(`refresh:${payload.userId}`);
  if (!stored || stored !== token) {
    throw new Error("Refresh token invalid or revoked");
  }

  const { accessToken, refreshToken } = issueTokens(payload.userId, payload.email);
  await cacheSet(`refresh:${payload.userId}`, refreshToken, REFRESH_TTL);

  return { accessToken, refreshToken };
}

// Called by the /refresh route — looks up stored token from Redis, issues new tokens
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

// ---------------------------------------------------------------------------

export function verifyAccessToken(token: string): AuthPayload {
  return jwt.verify(token, getSecret()) as AuthPayload;
}
