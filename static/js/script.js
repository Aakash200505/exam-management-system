document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');
  const toggle = document.querySelector('.sidebar-toggle');

  if (sidebar && toggle) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('is-open');
      if (backdrop) {
        backdrop.classList.toggle('visible');
      }
    });

    if (backdrop) {
      backdrop.addEventListener('click', () => {
        sidebar.classList.remove('is-open');
        backdrop.classList.remove('visible');
      });
    }
  }

  const examTimer = document.querySelector('#exam-timer');
  const form = document.querySelector('#exam-form');

  if (examTimer && form) {
    const deadline = Number(examTimer.dataset.start) * 1000 + Number(examTimer.dataset.duration) * 60000;
    const tick = () => {
      const seconds = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
      examTimer.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
      if (!seconds) {
        form.submit();
      }
    };
    tick();
    window.setInterval(tick, 1000);
  }

  document.querySelectorAll('.question-timer').forEach((timer) => {
    let remaining = Number(timer.dataset.seconds);
    const card = timer.closest('.question');
    const inputs = card ? card.querySelectorAll('input') : [];
    const tick = () => {
      timer.textContent = `${remaining}s`;
      if (remaining <= 0) {
        inputs.forEach((input) => {
          input.disabled = true;
        });
        return;
      }
      remaining -= 1;
      window.setTimeout(tick, 1000);
    };
    tick();
  });

  document.querySelectorAll('.alert').forEach((alert) => {
    window.setTimeout(() => alert.remove(), 5000);
  });
});

