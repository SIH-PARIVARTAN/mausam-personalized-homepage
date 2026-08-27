"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function RootPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (user) {
        router.push("/home");
      } else {
        router.push("/login");
      }
    }
  }, [user, loading, router]);

  return null; // Empty shell during redirect
}
