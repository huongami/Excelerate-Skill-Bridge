// Landing page (route "/"). Static markup only.
import { iconHtml as i, logoHtml } from "../core/dom.js";
import { isSignedIn } from "../api/index.js";

export async function landingView(root) {
  const signedIn = isSignedIn();
  root.innerHTML = `
  <nav class="top-nav" aria-label="Main">
    <div class="container">
      ${logoHtml("#/")}
      <div class="nav-links">
        <a href="#how">How it works</a>
        <a href="#talent">For talent</a>
        <a href="#employers">For employers</a>
      </div>
      <div class="nav-right">
        ${signedIn
          ? `<a href="#/home" class="btn btn-primary">Go to my workspace</a>`
          : `<a href="#/login" class="nav-login">Sign in</a><a href="#/signup" class="btn btn-primary">Get started</a>`}
      </div>
    </div>
  </nav>

  <main>
    <header class="hero">
      <span class="eyebrow hero-eyebrow">Skills-based hiring for <span class="au-chip">${i("map-pin")}Australia</span></span>
      <h1>Every skill, <em>recognised</em> — wherever it was built</h1>
      <p class="lead">
        Jinder translates overseas and cross-industry experience into the skills
        Australian employers look for — ranked, explained in plain language, and never a black box.
      </p>
      <div class="btn-row">
        <a href="#/signup" class="btn btn-primary btn-lg">Create free account ${i("arrow")}</a>
        <a href="#how" class="btn btn-secondary btn-lg">See how it works</a>
      </div>
      <p class="hero-note">Free for talent and employers during the pilot.</p>

      <div class="screenshot-frame" role="img" aria-label="Preview: a talent profile with overseas experience translated into Australian skill terms, with an 86% explained match for a Data Analyst role">
        <div class="frame-bar" aria-hidden="true"><i></i><i></i><i></i><span>jinder.app / talent / translation</span></div>
        <div class="frame-body" aria-hidden="true">
          <div>
            <div class="panel-title">Experience translation <span class="chip chip-pink">Cross-border</span></div>
            <div class="map-row"><span class="from">Product Owner, Hanoi</span>${i("arrow")}<span class="to">Agile delivery lead</span></div>
            <div class="map-row"><span class="from">BI Specialist, HCMC</span>${i("arrow")}<span class="to">Data Analyst</span></div>
            <div class="map-row"><span class="from">Informatica developer</span>${i("arrow")}<span class="to">ETL and ELT pipelines</span></div>
            <div class="map-row"><span class="from">B.Econ (VNU)</span>${i("arrow")}<span class="to">AQF Level 7 equivalent</span></div>
          </div>
          <div class="match-card">
            <div class="panel-title">Data Analyst · Sydney <span class="chip chip-green">Strong match</span></div>
            <div class="match-score">86%</div>
            <div class="meter"><span class="meter-86"></span></div>
            <div class="why">
              <div>${i("check")}Built Power BI dashboards for 6 teams</div>
              <div>${i("check")}SQL and Python for weekly reporting</div>
              <div class="gap">${i("alert")}Gap: Apache Airflow, about 1 month to learn</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="container market" aria-labelledby="marketTitle">
      <p class="eyebrow market-eyebrow">${i("map-pin")}The Australian job market</p>
      <h2 class="market-title" id="marketTitle">Skilled talent is here. Employers can't find it.</h2>
      <div class="stats">
        <div class="stat stat-talent">
          <span class="icon-tile pink">${i("graduation")}</span>
          <div><div class="stat-num">680,582</div><div class="stat-label">international students in Australia</div><div class="stat-src">Source: Dept. of Education, Jan–May 2026</div></div>
        </div>
        <div class="stat stat-employer">
          <span class="icon-tile blue">${i("briefcase")}</span>
          <div><div class="stat-num">69%</div><div class="stat-label">of employers struggle to find skilled talent</div><div class="stat-src">Source: ManpowerGroup, 2024</div></div>
        </div>
      </div>
    </section>

    <section class="band" id="how">
      <div class="container">
        <div class="section-intro">
          <span class="eyebrow">How it works</span>
          <h2 class="section-head">From overseas experience to a confident hire</h2>
        </div>
        <div class="grid-3">
          <article class="feature-card">
            <span class="step-num">01</span>
            <div class="icon-tile pink">${i("upload")}</div>
            <h3>Translate experience</h3>
            <p>Upload a CV. We map overseas job titles, qualifications and industry vocabulary to skills the Australian market recognises.</p>
          </article>
          <article class="feature-card">
            <span class="step-num">02</span>
            <div class="icon-tile yellow">${i("target")}</div>
            <h3>Check the gaps</h3>
            <p>Compare a translated profile against a real job description and see exactly which skills to strengthen.</p>
          </article>
          <article class="feature-card">
            <span class="step-num">03</span>
            <div class="icon-tile blue">${i("user-check")}</div>
            <h3>Decide with context</h3>
            <p>Employers see ranked matches with plain-language reasons. The analysis supports the decision — people make it.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="band band-soft">
      <div class="container grid-2">
        <article class="audience-card" id="talent">
          <div class="icon-tile accent">${i("globe")}</div>
          <h3>For international talent</h3>
          <ul class="check-list">
            <li>${i("check")}See your experience in the language local employers use</li>
            <li>${i("check")}Know your gaps before you apply</li>
            <li>${i("check")}Build one profile, reuse it for every role</li>
          </ul>
          <a href="#/signup?role=candidate" class="btn btn-primary btn-lg">Create my profile</a>
        </article>
        <article class="audience-card" id="employers">
          <div class="icon-tile green">${i("briefcase")}</div>
          <h3>For Australian employers</h3>
          <ul class="check-list">
            <li>${i("check")}Find qualified talent that keyword filters miss</li>
            <li>${i("check")}Explainable, ranked matches for every role</li>
            <li>${i("check")}Built for SMEs without large hiring teams</li>
          </ul>
          <a href="#/signup?role=recruiter" class="btn btn-secondary btn-lg">Start hiring</a>
        </article>
      </div>
    </section>

    <div class="container">
      <section class="cta-band-dark">
        <h2>No qualified person filtered out</h2>
        <p>Join as international talent or as an employer looking for skills that are already here.</p>
        <a href="#/signup" class="btn btn-on-dark btn-lg">Get started — it's free</a>
      </section>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          ${logoHtml("#/")}
          <p class="slogan">Where skills meet their match.</p>
          <p>Making skills visible, comparable and trustworthy — for the people who make hiring decisions.</p>
        </div>
        <div><h4>Product</h4><ul><li><a href="#how">How it works</a></li><li><a href="#talent">For talent</a></li><li><a href="#employers">For employers</a></li></ul></div>
        <div><h4>Account</h4><ul><li><a href="#/login">Sign in</a></li><li><a href="#/signup">Create account</a></li></ul></div>
        <div><h4>Company</h4><ul><li><a href="#/">About</a></li><li><a href="#/privacy" class="legal-link">Privacy</a></li><li><a href="#/terms" class="legal-link">Terms</a></li></ul></div>
      </div>
      <div class="footer-bottom">© 2026 Jinder. All rights reserved.</div>
    </div>
  </footer>`;
}
