"use client";

import { useEffect, useRef } from "react";
import Script from "next/script";

interface CredentialResponse {
  credential: string;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: CredentialResponse) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

interface Props {
  onToken: (idToken: string) => void;
}

export default function GoogleSignInButton({ onToken }: Props) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  function renderButton() {
    if (!window.google || !buttonRef.current || !clientId) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => onToken(response.credential),
    });
    window.google.accounts.id.renderButton(buttonRef.current, {
      type: "standard",
      theme: "outline",
      size: "large",
      width: 320,
      text: "continue_with",
    });
  }

  useEffect(() => {
    if (window.google) renderButton();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!clientId) return null;

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={renderButton}
      />
      <div ref={buttonRef} className="flex justify-center" />
    </>
  );
}
