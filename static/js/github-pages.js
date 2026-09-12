/*
 * Static GitHub Pages shell for Examora.
 * Flask remains the authoritative implementation for server features.
 */
(() => {
  const app = document.querySelector('#app');
  const header = document.querySelector('.public-nav');
  const accountKey = 'examora-pages-account';

  const home = () => `
    <main class="landing-page">
      <section class="hero">
        <div class="hero-copy">
          <span class="eyebrow">The modern exam platform</span>
          <h1>Make every assessment<br><em>count.</em></h1>
          <p>Create meaningful learning moments with intuitive tools for building, taking, and understanding assessments.</p>
          <div class="hero-actions">
            <a class="btn btn-primary btn-lg" href="#/register" data-route>Create your account <span aria-hidden="true">→</span></a>
            <a class="hero-link" href="#/login" data-route>I already have an account</a>
          </div>
        </div>
        <div class="hero-panel" aria-label="Platform overview">
          <div class="hero-panel-top"><span class="pulse-dot"></span><span>Assessment overview</span><span class="panel-date">Today</span></div>
          <div class="hero-score"><span>Average performance</span><strong>84<span>%</span></strong><small>↑ 12% from last assessment</small></div>
          <div class="mini-bars" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
          <div class="hero-panel-bottom"><span><b>24</b> active learners</span><span><b>6</b> assessments</span></div>
        </div>
      </section>
      <section class="features-section" aria-labelledby="workflow-title">
        <div class="section-intro"><span class="eyebrow">A simpler workflow</span><h2 id="workflow-title">Everything you need,<br>nothing you don’t.</h2></div>
        <div class="feature-grid">
          <article class="feature-card feature-build"><div class="feature-icon">✦</div><span class="feature-number">01</span><h3>Build</h3><p>Create courses, assessments, and question banks in one focused workspace.</p><div class="feature-line"></div><span class="feature-foot">Made for educators <b>→</b></span></article>
          <article class="feature-card feature-assess"><div class="feature-icon">✓</div><span class="feature-number">02</span><h3>Assess</h3><p>Deliver clear, timed exams that help students stay focused and confident.</p><div class="feature-line"></div><span class="feature-foot">Designed for focus <b>→</b></span></article>
          <article class="feature-card feature-understand"><div class="feature-icon">↗</div><span class="feature-number">03</span><h3>Understand</h3><p>Turn results into useful insight with progress, rankings, and analytics.</p><div class="feature-line"></div><span class="feature-foot">Insight at a glance <b>→</b></span></article>
        </div>
      </section>
    </main>`;

  const auth = (register) => `
    <div class="auth"><form class="panel form-panel" id="${register ? 'register' : 'login'}-form">
      <span class="eyebrow">${register ? 'JOIN EXAMORA' : 'ONLINE EXAM SYSTEM'}</span>
      <h1>${register ? 'Create account.' : 'Welcome back.'}</h1>
      ${register ? '<label>First Name<input class="form-control" name="first_name" required></label><label>Last Name<input class="form-control" name="last_name" required></label>' : ''}
      <label>Username<input class="form-control" name="username" required ${register ? '' : 'autofocus'}></label>
      <label>Password<input class="form-control" type="password" name="password" ${register ? 'minlength="10"' : ''} required>${register ? '<small>10+ characters, uppercase, lowercase, number, and special character.</small>' : ''}</label>
      ${register ? '<label>Confirm Password<input class="form-control" type="password" name="confirmation" required></label>' : ''}
      <label>${register ? 'Role' : 'Who are you?'}</label><div class="roles"><label><input type="radio" name="role" value="teacher" required> Teacher</label><label><input type="radio" name="role" value="student"> Student</label></div>
      <p class="alert alert-danger d-none" id="form-error" role="alert"></p>
      <button class="btn btn-primary w-100">${register ? 'REGISTER' : 'LOGIN'}</button>
      ${register ? '<p class="text-center mt-3">Already have an account? <a href="#/login" data-route>Sign in</a></p>' : '<p class="text-center mt-3">Don\'t have an account? <a href="#/register" data-route>Register</a></p>'}
    </form></div>`;

  const dashboard = (user) => `
    <div class="panel mt-5 p-4 p-md-5">
      <span class="eyebrow">${user.role.toUpperCase()} DASHBOARD</span>
      <h1>Welcome, ${escapeHtml(user.firstName)}.</h1>
      <p class="mb-4">You are viewing the static GitHub Pages version of Examora.</p>
      <div class="alert alert-warning mb-4">Courses, exams, results, uploads, email confirmations, and secure account validation require the Flask server and are not available on GitHub Pages.</div>
      <a class="btn btn-primary" href="#/" data-route>Return home</a>
      <button class="btn btn-outline-secondary ms-2" id="logout" type="button">Logout</button>
    </div>`;

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  const account = () => JSON.parse(localStorage.getItem(accountKey) || 'null');
  const showError = (message) => {
    const error = document.querySelector('#form-error');
    error.textContent = message;
    error.classList.remove('d-none');
  };

  function render() {
    const route = location.hash.replace(/^#/, '') || '/';
    const user = account();
    header.classList.toggle('d-none', route === '/dashboard');
    document.body.className = route === '/dashboard' ? 'app-body' : 'public-body';
    if (route === '/login') app.innerHTML = auth(false);
    else if (route === '/register') app.innerHTML = auth(true);
    else if (route === '/dashboard') app.innerHTML = user ? dashboard(user) : auth(false);
    else app.innerHTML = home();
    bind();
  }

  function bind() {
    document.querySelector('#register-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const values = new FormData(event.currentTarget);
      const password = values.get('password');
      if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$/.test(password)) return showError('Password must be at least 10 characters and include uppercase, lowercase, a number, and a special character.');
      if (password !== values.get('confirmation')) return showError('Passwords do not match.');
      localStorage.setItem(accountKey, JSON.stringify({ firstName: values.get('first_name'), username: values.get('username'), role: values.get('role') }));
      location.hash = '#/dashboard';
    });
    document.querySelector('#login-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const values = new FormData(event.currentTarget);
      const user = account();
      if (!user || user.username !== values.get('username') || user.role !== values.get('role')) return showError('Create a local demo account first, or use the Flask deployment to sign in to an existing account.');
      location.hash = '#/dashboard';
    });
    document.querySelector('#logout')?.addEventListener('click', () => { localStorage.removeItem(accountKey); location.hash = '#/'; });
  }

  window.addEventListener('hashchange', render);
  render();
})();
