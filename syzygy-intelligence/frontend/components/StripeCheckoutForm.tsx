"use client";

import { useState, useEffect, useRef } from "react";
import { Loader2, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { loadStripe, type Stripe, type StripeElements, type StripePaymentElement } from "@stripe/stripe-js";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";

let stripePromise: Promise<Stripe | null> | null = null;
function getStripe() {
  const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
  if (!key) return null;
  if (!stripePromise) stripePromise = loadStripe(key);
  return stripePromise;
}

interface StripeCheckoutFormProps {
  tier: "premium" | "enterprise";
  tierLabel: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function StripeCheckoutForm({ tier, tierLabel, onSuccess, onCancel }: StripeCheckoutFormProps) {
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const stripeRef = useRef<Stripe | null>(null);
  const elementsRef = useRef<StripeElements | null>(null);
  const elRef = useRef<StripePaymentElement | null>(null);

  useEffect(() => {
    initCheckout();
    return () => {
      if (elRef.current) {
        elRef.current.destroy();
        elRef.current = null;
      }
    };
  }, []);

  const initCheckout = async () => {
    try {
      const stripe = await getStripe();
      if (!stripe) {
        toast.error("Stripe is not configured");
        setLoading(false);
        return;
      }
      stripeRef.current = stripe;

      const headers = useAuthStore.getState().getAuthHeaders();
      const res = await fetch(`${API}/api/payments/create-setup-intent`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ tier }),
      });
      if (!res.ok) throw new Error("Failed to initialize payment");
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setCustomerId(data.customer_id);
      const elements = stripe.elements({
        clientSecret: data.client_secret,
        appearance: { theme: "night", variables: { colorPrimary: "#d4a853" } },
      });
      elementsRef.current = elements;
      const el = elements.create("payment", {
        fields: { billingDetails: { email: "never" } },
      });
      elRef.current = el;
      el.mount("#stripe-payment-element");
      el.on("ready", () => setReady(true));
    } catch (err: any) {
      toast.error(err.message || "Payment setup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    const stripe = stripeRef.current;
    const elements = elementsRef.current;
    if (!stripe || !elements || !customerId) return;
    setLoading(true);
    try {
      const { error, setupIntent } = await stripe.confirmSetup({
        elements,
        redirect: "if_required",
        confirmParams: { return_url: window.location.origin + "/settings" },
      });
      if (error) {
        toast.error(error.message || "Payment failed");
        setLoading(false);
        return;
      }
      if (!setupIntent?.payment_method) {
        toast.error("No payment method received");
        setLoading(false);
        return;
      }

      const headers = useAuthStore.getState().getAuthHeaders();
      const res = await fetch(`${API}/api/payments/activate-subscription`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          payment_method_id: setupIntent.payment_method,
          tier,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      toast.success(`Upgraded to ${tierLabel}!`);
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.message || "Subscription activation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-syzygy-gold" />
        </div>
      )}
      <div id="stripe-payment-element" className="min-h-[100px]" />
      <div className="flex gap-3 pt-2">
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 rounded-lg border border-syzygy-surface-border px-4 py-2 text-sm text-syzygy-grey hover:text-foreground transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={loading || !ready}
          className="flex-1 rounded-lg bg-syzygy-gold px-4 py-2 text-sm font-medium text-syzygy-obsidian hover:brightness-110 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <CreditCard className="h-4 w-4" />
          )}
          {loading ? "Processing..." : `Subscribe ${tierLabel}`}
        </button>
      </div>
    </div>
  );
}
