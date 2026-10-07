// Terms of Use ("/terms") and Privacy Policy ("/privacy"). Placeholder text.
import { logoHtml } from "../core/dom.js";

function page({ title, other, otherHref, note, body }) {
  return `
  <nav class="top-nav" aria-label="Main">
    <div class="container">
      ${logoHtml("#/")}
      <div class="nav-right"><a href="${otherHref}" class="legal-link">${other}</a></div>
    </div>
  </nav>
  <main class="legal-page">
    <span class="eyebrow">Legal</span>
    <h1>${title}</h1>
    <p class="updated">Last updated: 5 October 2026</p>
    <div class="legal-note" role="note">${note}</div>
    ${body}
  </main>
  <footer class="footer">
    <div class="container footer-bottom plain">© 2026 Jinder — Where skills meet their match. · <a href="${otherHref}" class="legal-link">${other}</a></div>
  </footer>`;
}

export async function termsView(root) {
  root.innerHTML = page({
    title: "Terms of Use", other: "Privacy Policy", otherHref: "#/privacy",
    note: "This is placeholder text. It is not a legal agreement. Replace it with terms reviewed by a lawyer before launch.",
    body: `
    <h2>1. About Jinder</h2>
    <p>Jinder helps international talent show their skills in terms that Australian employers recognise. It helps employers review talent with clear, explained matches.</p>
    <h2>2. Your account</h2>
    <ul>
      <li>Give correct information when you create an account.</li>
      <li>Keep your password private. You are responsible for activity on your account.</li>
      <li>You can close your account at any time.</li>
    </ul>
    <h2>3. How you can use the service</h2>
    <ul>
      <li>Upload only documents that you have the right to share.</li>
      <li>Do not upload false or misleading information.</li>
      <li>Do not use the service to discriminate against talent.</li>
    </ul>
    <h2>4. Decisions stay with people</h2>
    <p>Jinder gives decision support, not decisions. Employers make all hiring decisions. Match scores and skill translations are suggestions, and each one comes with its reasons.</p>
    <h2>5. Your content</h2>
    <p>You own the CVs, profiles and job descriptions that you upload. You give Jinder permission to process them only to provide the service to you.</p>
    <h2>6. Changes to these terms</h2>
    <p>We will tell you before we make important changes to these terms.</p>
    <h2>7. Contact</h2>
    <p>For questions about these terms, contact the Jinder team.</p>`,
  });
}

export async function privacyView(root) {
  root.innerHTML = page({
    title: "Privacy Policy", other: "Terms of Use", otherHref: "#/terms",
    note: "This is placeholder text. In this version, account data stays in your browser only and is not sent to a server. Replace this page with a reviewed policy before launch.",
    body: `
    <h2>1. Information we collect</h2>
    <ul>
      <li><strong>Account details:</strong> name, email, account type and, for employers, company name.</li>
      <li><strong>Profile content:</strong> CVs, work history and qualifications that you upload.</li>
      <li><strong>Role content:</strong> job descriptions that employers add.</li>
    </ul>
    <h2>2. How we use it</h2>
    <ul>
      <li>To translate experience into recognised skills.</li>
      <li>To compare profiles with roles and explain each match.</li>
      <li>To operate and improve the service.</li>
    </ul>
    <h2>3. Who can see your profile</h2>
    <p>You control who sees your profile. An employer sees your translated profile only after you share it or apply for their role.</p>
    <h2>4. Fairness</h2>
    <p>We do not use nationality, ethnicity, age, gender or visa type to score a match. Every score shows the skills and evidence behind it.</p>
    <h2>5. Your rights</h2>
    <p>You can ask to see, correct or delete your data at any time. We handle personal information in line with the Australian Privacy Principles.</p>
    <h2>6. Contact</h2>
    <p>For privacy questions, contact the Jinder team.</p>`,
  });
}
