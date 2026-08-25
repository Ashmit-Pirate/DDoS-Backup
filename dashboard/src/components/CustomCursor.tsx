"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import gsap from "gsap";

const CURSOR_SIZE = 22;
const CURSOR_SIZE_HOVER = 30;
const CURSOR_COLOR = "#8B6BB1";
const LAG_DURATION = 0.15;

export default function CustomCursor() {
  const followerRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  const [isFinePointer, setIsFinePointer] = useState(true);

  useEffect(() => {
    setMounted(true);
    const mq = window.matchMedia("(pointer: fine)");
    setIsFinePointer(mq.matches);
    
    const handler = (e: MediaQueryListEvent) => setIsFinePointer(e.matches);
    // Support older browsers that use addListener instead of addEventListener for MediaQueryList
    if (mq.addEventListener) {
      mq.addEventListener("change", handler);
    } else {
      mq.addListener(handler);
    }
    
    return () => {
      if (mq.removeEventListener) {
        mq.removeEventListener("change", handler);
      } else {
        mq.removeListener(handler);
      }
    };
  }, []);

  useEffect(() => {
    if (!mounted || !isFinePointer) return;

    const follower = followerRef.current;
    if (!follower) return;

    // Center initially so it doesn't animate from 0,0
    gsap.set(follower, { xPercent: -50, yPercent: -50, opacity: 0 });

    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const duration = isReducedMotion ? 0 : LAG_DURATION;

    // GSAP quickTo for highly performant tracking
    const xTo = gsap.quickTo(follower, "x", { duration, ease: "power2.out" });
    const yTo = gsap.quickTo(follower, "y", { duration, ease: "power2.out" });

    let isVisible = false;

    const onMouseMove = (e: MouseEvent) => {
      if (!isVisible) {
         gsap.set(follower, { opacity: 0.8 });
         isVisible = true;
         // Set immediate position on first interaction
         gsap.set(follower, { x: e.clientX, y: e.clientY });
      }
      xTo(e.clientX);
      yTo(e.clientY);
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest("a, button, input, select, [role='button'], .cursor-interactive")) {
        gsap.to(follower, { 
          width: CURSOR_SIZE_HOVER, 
          height: CURSOR_SIZE_HOVER, 
          borderWidth: 2,
          opacity: 0.9, 
          duration: isReducedMotion ? 0 : 0.2, 
          ease: "power2.out" 
        });
      }
    };
    
    const handleMouseOut = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest("a, button, input, select, [role='button'], .cursor-interactive")) {
        gsap.to(follower, { 
          width: CURSOR_SIZE, 
          height: CURSOR_SIZE, 
          borderWidth: 1.5,
          opacity: 0.8, 
          duration: isReducedMotion ? 0 : 0.2, 
          ease: "power2.out" 
        });
      }
    };

    const onMouseLeave = () => {
      isVisible = false;
      gsap.to(follower, { opacity: 0, duration: 0.2 });
    };

    window.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseover", handleMouseOver);
    document.addEventListener("mouseout", handleMouseOut);
    document.addEventListener("mouseleave", onMouseLeave);

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseover", handleMouseOver);
      document.removeEventListener("mouseout", handleMouseOut);
      document.removeEventListener("mouseleave", onMouseLeave);
    };
  }, [mounted, isFinePointer]);

  // Don't render anything until mounted on client, or on touch devices
  if (!mounted || !isFinePointer) return null;

  // Render into document.body using a Portal to completely escape ALL z-index contexts
  // and clipping (overflow: hidden) from parent elements like the NavigationRail or Layout
  return createPortal(
    <div 
      ref={followerRef}
      className="fixed top-0 left-0 rounded-full pointer-events-none z-[99999] opacity-0"
      style={{ 
        width: CURSOR_SIZE, 
        height: CURSOR_SIZE, 
        borderColor: CURSOR_COLOR,
        borderStyle: "solid",
        borderWidth: "1.5px",
        backgroundColor: "transparent",
      }}
    />,
    document.body
  );
}
