import { Navigate, Outlet, createFileRoute } from "@tanstack/react-router";
import { Loader } from "@/components/common/Loader";
import { useAuth } from "@/providers/AuthProvider";

export const Route = createFileRoute("/app")({
  component: AppLayoutRoute,
});

/**
 * Client-side mock route guard.
 * Later: validate the JWT (and refresh it) before rendering protected routes.
 */
function AppLayoutRoute() {
  const { user, hydrated } = useAuth();

  if (!hydrated) {
    return (
      <div className="grid min-h-screen place-items-center bg-background">
        <Loader label="Preparing your workspace" size={56} />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}