import { Suspense } from "react";
import CompleteAccountForm from "@/components/auth/CompleteAccountForm";

export default function CompleteAccountPage() {
  return (
    <Suspense>
      <CompleteAccountForm />
    </Suspense>
  );
}
