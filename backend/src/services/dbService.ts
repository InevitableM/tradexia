import { PrismaClient } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

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

class DbClient {
  readonly prisma: PrismaClient;

  constructor() {
    const adapter = new PrismaPg({
      connectionString: process.env.DATABASE_URL!,
    });
    this.prisma = new PrismaClient({ adapter, log: ["query", "error"] });
  }

  // -------------------------------------------------------------------------
  // findUserByEmail
  // -------------------------------------------------------------------------
  async findUserByEmail(email: string): Promise<UserRow | null> {
    console.log(`[dbService] findUserByEmail → ${email}`);
    const rows = await this.prisma.$queryRaw<UserRow[]>`
      SELECT id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
      FROM users
      WHERE email = ${email}
      LIMIT 1
    `;
    console.log(
      `[dbService] findUserByEmail ← ${rows[0] ? "found" : "not found"}`,
    );
    return rows[0] ?? null;
  }

  // -------------------------------------------------------------------------
  // findUserById
  // -------------------------------------------------------------------------
  async findUserById(id: string): Promise<UserRow | null> {
    const rows = await this.prisma.$queryRaw<UserRow[]>`
      SELECT id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
      FROM users
      WHERE id = ${id}::uuid
      LIMIT 1
    `;
    return rows[0] ?? null;
  }

  // -------------------------------------------------------------------------
  // createUser
  // -------------------------------------------------------------------------
  async createUser(input: CreateUserInput): Promise<UserRow> {
    console.log(
      `[dbService] createUser → email=${input.email} name=${input.name ?? null}`,
    );
    const { email, passwordHash, name } = input;
    const rows = await this.prisma.$queryRaw<UserRow[]>`
      INSERT INTO users (email, "passwordHash", name, "isVerified", "createdAt", "updatedAt")
      VALUES (${email}, ${passwordHash}, ${name ?? null}, false, NOW(), NOW())
      RETURNING id, email, "passwordHash", name, "isVerified", "verifiedAt", "createdAt", "updatedAt"
    `;
    console.log(`[dbService] createUser ← id=${rows[0].id}`);
    return rows[0];
  }

  // -------------------------------------------------------------------------
  // updateUser
  // -------------------------------------------------------------------------
  async updateUser(
    id: string,
    input: UpdateUserInput,
  ): Promise<UserRow | null> {
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

    if (fields.length === 0) return this.findUserById(id);

    // Build SET clause: "name = $1, password_hash = $2, updated_at = NOW()"
    const setClauses = fields.map((f, i) => `${f} = $${i + 1}`).join(", ");
    const query = `
      UPDATE users
      SET ${setClauses}, updated_at = NOW()
      WHERE id = $${fields.length + 1}::uuid
      RETURNING id, email, password_hash, name, created_at, updated_at
    `;

    const rows = await this.prisma.$queryRawUnsafe<UserRow[]>(
      query,
      ...values,
      id,
    );
    return rows[0] ?? null;
  }

  // -------------------------------------------------------------------------
  // markUserVerified
  // -------------------------------------------------------------------------
  async markUserVerified(id: string): Promise<void> {
    await this.prisma.$executeRaw`
      UPDATE users
      SET "isVerified" = true, "verifiedAt" = NOW(), "updatedAt" = NOW()
      WHERE id = ${id}::uuid
    `;
  }

  // -------------------------------------------------------------------------
  // deleteUser
  // -------------------------------------------------------------------------
  async deleteUser(id: string): Promise<boolean> {
    const result = await this.prisma.$executeRaw`
      DELETE FROM users
      WHERE id = ${id}::uuid
    `;
    return result > 0;
  }

  // -------------------------------------------------------------------------
  // Generic escape hatches for one-off/composed queries (e.g. from backendSdk).
  //
  // ALWAYS use parameterized placeholders ($1, $2, ...) with the params array —
  // never interpolate values directly into the query string. These wrap
  // $queryRawUnsafe/$executeRawUnsafe, which do NOT sanitize the query text
  // itself, only the params.
  // -------------------------------------------------------------------------

  async runQuery<T = unknown>(
    query: string,
    params: unknown[] = [],
  ): Promise<T[]> {
    return this.prisma.$queryRawUnsafe<T[]>(query, ...params);
  }

  async runCommand(query: string, params: unknown[] = []): Promise<number> {
    return this.prisma.$executeRawUnsafe(query, ...params);
  }
}

// Instantiated once here so every importer shares the single underlying
// PrismaClient/connection pool. Only the methods listed below are part of
// the public surface — anything not exposed here isn't reachable as `db.x`,
// even though it exists on the underlying instance.
const client = new DbClient();

export const db = {
  prisma: client.prisma,
  findUserByEmail: client.findUserByEmail.bind(client),
  findUserById: client.findUserById.bind(client),
  createUser: client.createUser.bind(client),
  updateUser: client.updateUser.bind(client),
  markUserVerified: client.markUserVerified.bind(client),
  deleteUser: client.deleteUser.bind(client),
  runQuery: client.runQuery.bind(client),
  runCommand: client.runCommand.bind(client),
};
