"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const hasSession = !!localStorage.getItem("accessToken");
    router.replace(hasSession ? "/chat" : "/auth/login");
  }, [router]);

  return null;
}
