document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const target = document.querySelector(button.dataset.target);
      if (!target) return;

      const isHidden = target.classList.toggle('is-hidden');
      button.textContent = isHidden ? '표 펼치기' : '표 접기';
    });
  });
});
