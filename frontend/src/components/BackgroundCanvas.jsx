import { useRef, useEffect } from 'react';

const PARTICLE_COUNT = 100;
const CONNECTION_DISTANCE = 150;
const MOUSE_DISTANCE = 200;
const COLORS = ['#5227FF', '#FF9FFC', '#B19EEF'];

export default function BackgroundCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    let mouse = { x: null, y: null };
    let animationId;

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 1.5;
        this.vy = (Math.random() - 0.5) * 1.5;
        this.size = Math.random() * 2 + 1;
        this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
        if (mouse.x != null) {
          let dx = mouse.x - this.x;
          let dy = mouse.y - this.y;
          let distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < MOUSE_DISTANCE) {
            const force = (MOUSE_DISTANCE - distance) / MOUSE_DISTANCE;
            this.vx -= (dx / distance) * force * 0.6;
            this.vy -= (dy / distance) * force * 0.6;
          }
        }
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      }
    }

    function initParticles() {
      particles = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
      }
    }

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initParticles();
    }

    function animate() {
      animationId = requestAnimationFrame(animate);
      ctx.clearRect(0, 0, width, height);

      particles.forEach(p => { p.update(); p.draw(); });

      for (let a = 0; a < particles.length; a++) {
        for (let b = a; b < particles.length; b++) {
          let dx = particles[a].x - particles[b].x;
          let dy = particles[a].y - particles[b].y;
          let distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < CONNECTION_DISTANCE) {
            let opacity = 1 - (distance / CONNECTION_DISTANCE);
            ctx.strokeStyle = `rgba(177, 158, 239, ${opacity * 0.5})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(particles[a].x, particles[a].y);
            ctx.lineTo(particles[b].x, particles[b].y);
            ctx.stroke();
          }
        }
      }

      if (mouse.x != null) {
        for (let i = 0; i < particles.length; i++) {
          let dx = mouse.x - particles[i].x;
          let dy = mouse.y - particles[i].y;
          let distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < MOUSE_DISTANCE) {
            let opacity = 1 - (distance / MOUSE_DISTANCE);
            ctx.strokeStyle = `rgba(82, 39, 255, ${opacity * 0.8})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(mouse.x, mouse.y);
            ctx.lineTo(particles[i].x, particles[i].y);
            ctx.stroke();
          }
        }
      }
    }

    const handleMouseMove = (e) => { mouse.x = e.x; mouse.y = e.y; };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', resize);

    resize();
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} id="bgCanvas" />;
}
