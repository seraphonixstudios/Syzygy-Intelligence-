export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="mb-8 text-3xl font-bold text-syzygy-gold">Terms of Service</h1>
      <div className="space-y-6 text-sm leading-relaxed text-syzygy-grey-light/80">
        <p>
          <strong className="text-syzygy-grey-light">Effective date:</strong> June 18, 2026
        </p>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">1. Acceptance of Terms</h2>
          <p>
            By accessing or using Syzygy Intelligence, you agree to be bound by these Terms of Service. If you do not
            agree, do not use the service.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">2. Description of Service</h2>
          <p>
            Syzygy Intelligence provides an AI-powered multi-agent platform that enables users to create, configure,
            and interact with AI agents for various tasks including chat, research, coding, content generation, and
            consensus-based decision making.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">3. User Accounts</h2>
          <p>
            You are responsible for maintaining the confidentiality of your account credentials. You must provide
            accurate information and keep it up to date. You may not share your account with others.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">4. Subscriptions and Payments</h2>
          <p>
            Subscription fees are billed in advance on a monthly basis. All payments are processed securely through
            Stripe. Refunds are provided at our discretion. We may change pricing with 30 days&apos; notice.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">5. Acceptable Use</h2>
          <p>
            You agree not to use the service for illegal activities, to generate harmful content, to circumvent
            access controls, or to interfere with the operation of the platform.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">6. Limitation of Liability</h2>
          <p>
            Syzygy Intelligence is provided &ldquo;as is&rdquo; without warranties of any kind. We are not liable for
            damages arising from your use of the service, to the maximum extent permitted by law.
          </p>
        </section>
        <section>
          <h2 className="mb-3 text-xl font-semibold text-syzygy-grey-light">7. Contact</h2>
          <p>
            For questions about these terms, contact us at{" "}
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
