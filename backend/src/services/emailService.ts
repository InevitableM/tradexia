const TOKEN_URL = "https://oauth2.googleapis.com/token";
const SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send";

async function getAccessToken(): Promise<string> {
  const clientId = process.env.GMAIL_CLIENT_ID;
  const clientSecret = process.env.GMAIL_CLIENT_SECRET;
  const refreshToken = process.env.GMAIL_REFRESH_TOKEN;

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error("GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN must be set");
  }

  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: "refresh_token",
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Gmail token refresh failed ${res.status}: ${body}`);
  }

  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

function toBase64Url(input: string): string {
  return Buffer.from(input)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function buildMimeMessage(opts: {
  from: string;
  to: string;
  subject: string;
  text: string;
  html: string;
}): string {
  const boundary = "tradexia_boundary";
  const lines = [
    `From: ${opts.from}`,
    `To: ${opts.to}`,
    `Subject: ${opts.subject}`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    "",
    `--${boundary}`,
    "Content-Type: text/plain; charset=UTF-8",
    "",
    opts.text,
    "",
    `--${boundary}`,
    "Content-Type: text/html; charset=UTF-8",
    "",
    opts.html,
    "",
    `--${boundary}--`,
  ];
  return lines.join("\r\n");
}

export async function sendVerificationEmail(
  toEmail: string,
  token: string
): Promise<void> {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:4000";
  const verifyUrl = `${backendUrl}/api/auth/verify?token=${token}`;
  const fromName = process.env.SMTP_FROM_NAME || "Tradexia";
  const fromEmail = process.env.GMAIL_SENDER;

  if (!fromEmail) throw new Error("GMAIL_SENDER must be set");

  console.log(`[emailService] sendVerificationEmail → sending to ${toEmail} via Gmail API`);
  const startedAt = Date.now();

  try {
    const accessToken = await getAccessToken();

    const raw = buildMimeMessage({
      from: `${fromName} <${fromEmail}>`,
      to: toEmail,
      subject: "Verify your Tradexia account",
      text: `Click the link below to verify your email address. It expires in 24 hours.\n\n${verifyUrl}\n\nIf you didn't sign up, ignore this email.`,
      html: `
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
          <h2 style="margin:0 0 8px;font-size:20px;color:#111">Verify your email</h2>
          <p style="margin:0 0 24px;color:#555;font-size:14px;line-height:1.6">
            Thanks for signing up for Tradexia. Click the button below to verify
            your email address. This link expires in <strong>24 hours</strong>.
          </p>
          <a href="${verifyUrl}"
             style="display:inline-block;padding:12px 24px;background:#030213;color:#fff;
                    text-decoration:none;border-radius:8px;font-size:14px;font-weight:500">
            Verify email
          </a>
          <p style="margin:24px 0 0;color:#999;font-size:12px">
            If you didn't create an account, you can safely ignore this email.
          </p>
        </div>
      `,
    });

    const res = await fetch(SEND_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ raw: toBase64Url(raw) }),
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Gmail API error ${res.status}: ${body}`);
    }

    console.log(`[emailService] sendVerificationEmail ← sent to ${toEmail} in ${Date.now() - startedAt}ms`);
  } catch (err) {
    console.error(`[emailService] sendVerificationEmail ✗ failed after ${Date.now() - startedAt}ms:`, err);
    throw err;
  }
}
