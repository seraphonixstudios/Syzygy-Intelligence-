export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="mb-8 text-3xl font-bold text-syzygy-gold">Privacy Policy</h1>
      <div className="space-y-6 text-sm leading-relaxed text-syzygy-grey-light/80">
        <p>
          <strong className="text-syzygy-grey-light">Effective date:</strong> June 18, 2026
        </p>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">1. Information We Collect</h2>
          <p>
            We collect information you provide when creating an account, including your email address and display name.
            When you use our services, we process messages, files, and agent configurations you submit. Payment processing
            is handled securely by Stripe — we never store full payment card details.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">2. How We Use Your Information</h2>
          <p>
            Your information is used to provide, maintain, and improve our AI agent platform; to process subscriptions
            and payments; to send service-related communications; and to comply with legal obligations.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">3. Data Sharing</h2>
          <p>
            We do not sell your personal data. We share data with trusted third-party service providers (Stripe for
            payments, SendGrid for email, GitHub for OAuth authentication) only as necessary to deliver our services.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">4. Data Retention</h2>
          <p>
            We retain your account data for as long as your account is active. You may request deletion of your account
            and associated data by contacting us at the address below.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">5. Contact</h2>
          <p>
            For privacy inquiries, contact us at{" "}
            <a href="mailto:seraphonixstudios@gmail.com" className="text-syzygy-gold hover:underline">
              seraphonixstudios@gmail.com
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
