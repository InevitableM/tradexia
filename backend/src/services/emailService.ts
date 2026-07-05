import nodemailer from "nodemailer";

function getTransport() {
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;
  const host = process.env.SMTP_HOST || "smtp.gmail.com";
  const port = Number(process.env.SMTP_PORT) || 587;

  if (!user || !pass) throw new Error("SMTP_USER and SMTP_PASS must be set");

  return nodemailer.createTransport({
    host,
    port,
    secure: port === 465,
    auth: { user, pass },
    connectionTimeout: 10_000,
    greetingTimeout: 10_000,
    socketTimeout: 10_000,
  });
}

export async function sendVerificationEmail(
  toEmail: string,
  token: string
): Promise<void> {
  const frontendUrl = process.env.FRONTEND_URL || "http://localhost:3000";
  const backendUrl  = process.env.BACKEND_URL   || "http://localhost:4000";
  const verifyUrl   = `${backendUrl}/api/auth/verify?token=${token}`;
  const fromName    = process.env.SMTP_FROM_NAME  || "Tradexia";
  const fromEmail   = process.env.SMTP_USER!;

  const smtpHost = process.env.SMTP_HOST || "smtp.gmail.com";
  const smtpPort = Number(process.env.SMTP_PORT) || 587;
  console.log(`[emailService] sendVerificationEmail → connecting to ${smtpHost}:${smtpPort} to send to ${toEmail}`);
  const startedAt = Date.now();

  try {
    await getTransport().sendMail({
      from: `"${fromName}" <${fromEmail}>`,
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
    console.log(`[emailService] sendVerificationEmail ← sent to ${toEmail} in ${Date.now() - startedAt}ms`);
  } catch (err) {
    console.error(`[emailService] sendVerificationEmail ✗ failed after ${Date.now() - startedAt}ms:`, err);
    throw err;
  }
}
