import { ClientForm } from "@/components/clients/ClientForm";

export default function NewClientPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New Client</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Add a new client to start their CMA preparation
        </p>
      </div>
      <ClientForm />
    </div>
  );
}
