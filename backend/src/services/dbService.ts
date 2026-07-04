import { PrismaClient } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({
  adapter,
  log: ["query", "error"],
});

export interface UserRow {
  id: string;
  email: string;
  passwordHash: string;
  name: string | null;
  isVerified: boolean;
  verifiedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateUserInput {
  email: string;
  passwordHash: string;
  name?: string;
}

export interface UpdateUserInput {
  name?: string;
  passwordHash?: string;
}

// ---------------------------------------------------------------------------
// findUserByEmail
// ---------------------------------------------------------------------------
export async function findUserByEmail(email: string): Promise<UserRow | null> {
  console.log(`[dbService] findUserByEmail → ${email}`);
  const rows = await prisma.$queryRaw<UserRow[]>`
    SELECT id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
    FROM users
    WHERE email = ${email}
    LIMIT 1
  `;
  console.log(`[dbService] findUserByEmail ← ${rows[0] ? "found" : "not found"}`);
  return rows[0] ?? null;
}

// ---------------------------------------------------------------------------
// findUserById
// ---------------------------------------------------------------------------
export async function findUserById(id: string): Promise<UserRow | null> {
  const rows = await prisma.$queryRaw<UserRow[]>`
    SELECT id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
    FROM users
    WHERE id = ${id}::uuid
    LIMIT 1
  `;
  return rows[0] ?? null;
}

// ---------------------------------------------------------------------------
// createUser
// ---------------------------------------------------------------------------
export async function createUser(input: CreateUserInput): Promise<UserRow> {
  console.log(`[dbService] createUser → email=${input.email} name=${input.name ?? null}`);
  const { email, passwordHash, name } = input;
  const rows = await prisma.$queryRaw<UserRow[]>`
    INSERT INTO users (email, "passwordHash", name, "isVerified", "createdAt", "updatedAt")
    VALUES (${email}, ${passwordHash}, ${name ?? null}, false, NOW(), NOW())
    RETURNING id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
  `;
  console.log(`[dbService] createUser ← id=${rows[0].id}`);
  return rows[0];
}

// ---------------------------------------------------------------------------
// updateUser
// ---------------------------------------------------------------------------
export async function updateUser(id: string, input: UpdateUserInput): Promise<UserRow | null> {
  const fields: string[] = [];
  const values: unknown[] = [];

  if (input.name !== undefined) {
    fields.push("name");
    values.push(input.name);
  }
  if (input.passwordHash !== undefined) {
    fields.push('"passwordHash"');
    values.push(input.passwordHash);
  }

  if (fields.length === 0) return findUserById(id);

  // Build SET clause: "name = $1, password_hash = $2, updated_at = NOW()"
  const setClauses = fields.map((f, i) => `${f} = $${i + 1}`).join(", ");
  const query = `
    UPDATE users
    SET ${setClauses}, updated_at = NOW()
    WHERE id = $${fields.length + 1}::uuid
    RETURNING id, email, password_hash, name, created_at, updated_at
  `;

  const rows = await prisma.$queryRawUnsafe<UserRow[]>(query, ...values, id);
  return rows[0] ?? null;
}

// ---------------------------------------------------------------------------
// markUserVerified
// ---------------------------------------------------------------------------
export async function markUserVerified(id: string): Promise<void> {
  await prisma.$executeRaw`
    UPDATE users
    SET "isVerified" = true, "verifiedAt" = NOW(), "updatedAt" = NOW()
    WHERE id = ${id}::uuid
  `;
}

// ---------------------------------------------------------------------------
// deleteUser
// ---------------------------------------------------------------------------
export async function deleteUser(id: string): Promise<boolean> {
  const result = await prisma.$executeRaw`
    DELETE FROM users
    WHERE id = ${id}::uuid
  `;
  return result > 0;
}
