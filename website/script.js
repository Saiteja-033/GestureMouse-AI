/**
 * GestureMouse AI - Website Interactive Logic
 * Features an interactive blade-slicing canvas simulator in the hero section,
 * tab switcher, mobile navigation, and configurable GitHub release links.
 */

// ============================================================================
// CONFIGURATION & RELEASE METRICS (Configurable URLs)
// ============================================================================
const CONFIG = {
  GITHUB_REPO_URL: "https://github.com/Saiteja-033/GestureMouse-AI",
  RELEASE_VERSION: "v1.0.0",
  // Direct GitHub release binary download asset
  WINDOWS_DOWNLOAD_URL: "https://github.com/Saiteja-033/GestureMouse-AI/releases/download/v1.0.0/GestureMouseAI-Windows-x64.zip",
  FILE_SIZE: "~148 MB (Standalone Zip)",
};

document.addEventListener("DOMContentLoaded", () => {
  initNavbar();
  initDownloadLinks();
  initTabs();
  initHeroInteractiveCanvas();
});

// ============================================================================
// 1. Navigation & Mobile Menu
// ============================================================================
function initNavbar() {
  const navbar = document.querySelector(".navbar");
  const menuToggle = document.querySelector(".menu-toggle");
  const navLinks = document.querySelector(".nav-links");

  window.addEventListener("scroll", () => {
    if (window.scrollY > 40) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  });

  if (menuToggle && navLinks) {
    menuToggle.addEventListener("click", () => {
      navLinks.classList.toggle("active");
    });

    navLinks.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("active");
      });
    });
  }
}

// ============================================================================
// 2. Download Buttons & Configurable Links
// ============================================================================
function initDownloadLinks() {
  const downloadBtns = document.querySelectorAll(".download-trigger");
  const githubBtns = document.querySelectorAll(".github-trigger");
  const versionTags = document.querySelectorAll(".release-version-tag");
  const sizeTags = document.querySelectorAll(".release-size-tag");

  downloadBtns.forEach(btn => {
    btn.setAttribute("href", CONFIG.WINDOWS_DOWNLOAD_URL);
    btn.setAttribute("target", "_blank");
  });

  githubBtns.forEach(btn => {
    btn.setAttribute("href", CONFIG.GITHUB_REPO_URL);
    btn.setAttribute("target", "_blank");
  });

  versionTags.forEach(tag => {
    tag.textContent = CONFIG.RELEASE_VERSION;
  });

  sizeTags.forEach(tag => {
    tag.textContent = CONFIG.FILE_SIZE;
  });
}

// ============================================================================
// 3. Demo Tabs
// ============================================================================
function initTabs() {
  const tabBtns = document.querySelectorAll(".demo-tab-btn");
  const tabPanels = document.querySelectorAll(".demo-panel");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;

      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(p => (p.style.display = "none"));

      btn.classList.add("active");
      const targetPanel = document.getElementById(target);
      if (targetPanel) {
        targetPanel.style.display = "block";
      }
    });
  });
}

// ============================================================================
// 4. Hero Interactive Canvas Simulation (Virtual Slicing & Hand Skeleton)
// ============================================================================
function initHeroInteractiveCanvas() {
  const canvas = document.getElementById("heroInteractiveCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let width = (canvas.width = canvas.parentElement.clientWidth);
  let height = (canvas.height = canvas.parentElement.clientHeight);

  window.addEventListener("resize", () => {
    if (!canvas.parentElement) return;
    width = canvas.width = canvas.parentElement.clientWidth;
    height = canvas.height = canvas.parentElement.clientHeight;
  });

  // Trail points
  const trail = [];
  const maxTrail = 16;

  // Simulated floating fruits
  const fruits = [
    { x: width * 0.25, y: height * 0.6, vx: 1.2, vy: -1.0, radius: 26, emoji: "🍉", color: "#FF3366", sliced: false },
    { x: width * 0.5, y: height * 0.7, vx: -0.8, vy: -1.4, radius: 22, emoji: "🍊", color: "#FFA500", sliced: false },
    { x: width * 0.75, y: height * 0.5, vx: 1.0, vy: 1.2, radius: 20, emoji: "🍎", color: "#FF2A2A", sliced: false },
    { x: width * 0.4, y: height * 0.35, vx: -1.4, vy: 0.9, radius: 24, emoji: "🍌", color: "#FFD700", sliced: false },
  ];

  // Particles
  const particles = [];

  let mouseX = width / 2;
  let mouseY = height / 2;
  let hasUserInteracted = false;

  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
    hasUserInteracted = true;
    addTrailPoint(mouseX, mouseY);
    checkSlice(mouseX, mouseY);
  });

  function addTrailPoint(x, y) {
    trail.push({ x, y, time: performance.now() });
    if (trail.length > maxTrail) {
      trail.shift();
    }
  }

  function checkSlice(x, y) {
    if (trail.length < 2) return;
    const p1 = trail[trail.length - 2];
    const p2 = trail[trail.length - 1];

    fruits.forEach(f => {
      if (!f.sliced) {
        const dist = Math.hypot(f.x - x, f.y - y);
        if (dist < f.radius + 12) {
          f.sliced = true;
          // Spawn particles
          for (let i = 0; i < 18; i++) {
            particles.push({
              x: f.x,
              y: f.y,
              vx: (Math.random() - 0.5) * 8,
              vy: (Math.random() - 0.5) * 8 - 2,
              radius: Math.random() * 4 + 2,
              color: f.color,
              alpha: 1.0,
            });
          }
          // Reset fruit after 2.5s
          setTimeout(() => {
            f.sliced = false;
            f.y = height + 30;
            f.vy = -Math.random() * 2 - 2;
          }, 2500);
        }
      }
    });
  }

  // Animation Loop
  let lastTime = performance.now();
  function animate(now) {
    const dt = (now - lastTime) / 1000;
    lastTime = now;

    // Simulated auto hand trajectory if user has not interacted
    if (!hasUserInteracted) {
      const autoX = width / 2 + Math.cos(now * 0.002) * (width * 0.32);
      const autoY = height / 2 + Math.sin(now * 0.003) * (height * 0.28);
      addTrailPoint(autoX, autoY);
      checkSlice(autoX, autoY);
    }

    ctx.clearRect(0, 0, width, height);

    // 1. Draw Active Boundary Box
    const padX = 50;
    const padY = 40;
    ctx.strokeStyle = "rgba(0, 229, 255, 0.25)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 6]);
    ctx.strokeRect(padX, padY, width - 2 * padX, height - 2 * padY);
    ctx.setLineDash([]);

    // 2. Update & Draw Fruits
    fruits.forEach(f => {
      f.x += f.vx;
      f.y += f.vy;

      // Bounce inside canvas
      if (f.x < f.radius + padX || f.x > width - f.radius - padX) f.vx *= -1;
      if (f.y < f.radius + padY || f.y > height - f.radius - padY) f.vy *= -1;

      if (!f.sliced) {
        ctx.font = `${f.radius * 1.6}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(f.emoji, f.x, f.y);

        // Subtle target ring
        ctx.beginPath();
        ctx.arc(f.x, f.y, f.radius + 6, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
        ctx.lineWidth = 1;
        ctx.stroke();
      } else {
        // Draw sliced halves floating apart
        ctx.font = `${f.radius * 1.1}px sans-serif`;
        ctx.fillText("✨", f.x - 10, f.y - 10);
        ctx.fillText("✨", f.x + 10, f.y + 10);
      }
    });

    // 3. Update & Draw Particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.15; // gravity
      p.alpha -= 0.02;

      if (p.alpha <= 0) {
        particles.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // 4. Draw Glowing Virtual Blade Trail
    if (trail.length >= 2) {
      for (let i = 0; i < trail.length - 1; i++) {
        const p1 = trail[i];
        const p2 = trail[i + 1];
        const progress = (i + 1) / trail.length;

        // Outer glow
        ctx.strokeStyle = `rgba(0, 229, 255, ${progress * 0.7})`;
        ctx.lineWidth = progress * 10;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        // Inner core
        ctx.strokeStyle = `rgba(255, 255, 255, ${progress})`;
        ctx.lineWidth = progress * 3.5;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      // Tip sparkle
      const tip = trail[trail.length - 1];
      ctx.fillStyle = "#00E5FF";
      ctx.beginPath();
      ctx.arc(tip.x, tip.y, 6, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#FFFFFF";
      ctx.beginPath();
      ctx.arc(tip.x, tip.y, 3, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}
