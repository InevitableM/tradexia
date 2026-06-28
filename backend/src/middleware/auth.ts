import { Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { AuthRequest, AuthPayload } from "../types";

export function authenticate(req: AuthRequest, _res: Response, next: NextFunction): void {
  // TODO: re-enable JWT verification once auth flow is finalized
  req.user = { userId: "dev_user", email: "dev@tradexia.com" };
  next();
}

export function generateTokens(userId: string, email: string) {
  const secret = process.env.JWT_SECRET!;
  const expiresIn = (process.env.JWT_EXPIRES_IN || "7d") as jwt.SignOptions["expiresIn"];
  const refreshExpiresIn = (process.env.JWT_REFRESH_EXPIRES_IN || "30d") as jwt.SignOptions["expiresIn"];

  const accessToken = jwt.sign({ userId, email }, secret, { expiresIn });
  const refreshToken = jwt.sign({ userId, email }, secret, { expiresIn: refreshExpiresIn });

  return { accessToken, refreshToken };
}

export function verifyRefreshToken(token: string): AuthPayload {
  const secret = process.env.JWT_SECRET!;
  return jwt.verify(token, secret) as AuthPayload;
}
