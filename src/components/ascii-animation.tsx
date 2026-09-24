import { useEffect, useRef, useState } from "react";

class AnimationManager {
	private _animation: number | null = null;
	private callback: () => void;
	private lastFrame = -1;
	private accumulator = 0;
	private frameTime = 1000 / 30;

	constructor(callback: () => void, fps = 30) {
		this.callback = callback;
		this.frameTime = 1000 / fps;
	}

	updateFPS(fps: number) {
		this.frameTime = 1000 / fps;
	}

	start() {
		if (this._animation != null) return;
		this._animation = requestAnimationFrame(this.update);
	}

	pause() {
		if (this._animation == null) return;
		this.lastFrame = -1;
		this.accumulator = 0;
		cancelAnimationFrame(this._animation);
		this._animation = null;
	}

	private update = (time: number) => {
		if (this._animation == null) return;
		if (this.lastFrame === -1) {
			this.lastFrame = time;
		} else {
			this.accumulator += time - this.lastFrame;
			this.lastFrame = time;

			// Avanzar la cantidad de frames correspondiente, arrastrando el
			// excedente al siguiente tick para mantener un ritmo estable.
			const maxSteps = 3;
			let steps = 0;
			while (this.accumulator >= this.frameTime && steps < maxSteps) {
				this.callback();
				this.accumulator -= this.frameTime;
				steps++;
			}
			if (this.accumulator > this.frameTime) {
				this.accumulator = 0;
			}
		}
		this._animation = requestAnimationFrame(this.update);
	};
}

function frameBounds(frames: string[], pad: number) {
	if (frames.length === 0) {
		return { top: 0, bottom: 0, left: 0, right: 0 };
	}

	let top = Infinity;
	let bottom = -Infinity;
	let left = Infinity;
	let right = -Infinity;

	for (const frame of frames) {
		const lines = frame.split("\n");
		if (lines.length > 0 && lines[lines.length - 1] === "") lines.pop();
		lines.forEach((line, row) => {
			for (let col = 0; col < line.length; col++) {
				if (line[col] !== " ") {
					if (row < top) top = row;
					if (row > bottom) bottom = row;
					if (col < left) left = col;
					if (col > right) right = col;
				}
			}
		});
	}

	if (top === Infinity) {
		return { top: 0, bottom: 0, left: 0, right: 0 };
	}

	return {
		top: Math.max(0, top - pad),
		bottom: bottom + pad,
		left: Math.max(0, left - pad),
		right: right + pad,
	};
}

// Recorta todas las frames a la caja global de contenido (unión entre
// frames) más un pequeño margen, para que la animación quede compacta sin
// que el contenido baile de posición entre frames.
function trimFrames(frames: string[], pad = 1): string[] {
	const { top, bottom, left, right } = frameBounds(frames, pad);
	return frames.map((frame) => {
		const lines = frame.split("\n");
		if (lines.length > 0 && lines[lines.length - 1] === "") lines.pop();
		return lines
			.slice(top, bottom + 1)
			.map((line) => line.slice(left, right + 1))
			.join("\n");
	});
}

interface ASCIIAnimationProps {
	frames?: string[];
	className?: string;
	fps?: number;
	colorOverlay?: boolean;
	frameCount?: number;
	frameFolder?: string;
	size?: string;
}

export default function ASCIIAnimation({
	frames: providedFrames,
	className = "",
	fps = 24,
	colorOverlay = false,
	frameCount = 60,
	frameFolder = "frames",
	size = "12px",
}: ASCIIAnimationProps) {
	const [frames, setFrames] = useState<string[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [currentFrame, setCurrentFrame] = useState(0);
	const framesRef = useRef<string[]>([]);

	const [animationManager] = useState(
		() =>
			new AnimationManager(() => {
				setCurrentFrame((current) => {
					if (framesRef.current.length === 0) return current;
					return (current + 1) % framesRef.current.length;
				});
			}, fps),
	);

	useEffect(() => {
		const resolveFrameCount = async (): Promise<number | null> => {
			try {
				const response = await fetch(`/${frameFolder}/frames.json`);
				if (!response.ok) return null;
				const manifest = (await response.json()) as { count?: number };
				if (typeof manifest.count === "number" && manifest.count > 0) {
					return manifest.count;
				}
			} catch {
				// Ignorar y usar el frameCount provisto.
			}
			return null;
		};

		const loadFrames = async () => {
			if (providedFrames) {
				const trimmed = trimFrames(providedFrames);
				setFrames(trimmed);
				framesRef.current = trimmed;
				setIsLoading(false);
				return;
			}

			try {
				const manifestCount = await resolveFrameCount();
				const totalCount = manifestCount ?? frameCount;
				const frameFiles = Array.from(
					{ length: totalCount },
					(_, i) => `frame_${String(i + 1).padStart(4, "0")}.txt`,
				);

				const framePromises = frameFiles.map(async (filename) => {
					const response = await fetch(`/${frameFolder}/${filename}`);
					if (!response.ok) {
						throw new Error(`Failed to fetch ${filename}: ${response.status}`);
					}
					return await response.text();
				});

				const loadedFrames = await Promise.all(framePromises);
				console.log(`Loaded ${loadedFrames.length} frames`);
				const trimmed = trimFrames(loadedFrames);
				setFrames(trimmed);
				framesRef.current = trimmed;
				setCurrentFrame(0);
			} catch (error) {
				console.error("Failed to load ASCII frames:", error);
			} finally {
				setIsLoading(false);
			}
		};

		loadFrames();
	}, [providedFrames]);

	useEffect(() => {
		animationManager.updateFPS(fps);
	}, [fps, animationManager]);

	useEffect(() => {
		if (frames.length === 0) return;

		const reducedMotion =
			window.matchMedia(`(prefers-reduced-motion: reduce)`).matches === true;

		if (reducedMotion) {
			return;
		}

		const handleVisibilityChange = () => {
			if (document.hidden) {
				animationManager.pause();
			} else {
				animationManager.start();
			}
		};

		document.addEventListener("visibilitychange", handleVisibilityChange);

		if (!document.hidden) {
			animationManager.start();
		}

		return () => {
			document.removeEventListener("visibilitychange", handleVisibilityChange);
			animationManager.pause();
		};
	}, [animationManager, frames.length]);

	if (isLoading) {
		return (
			<div className={`font-mono whitespace-pre overflow-hidden ${className}`}>
				Loading ASCII animation...
			</div>
		);
	}

	if (!frames.length) {
		return (
			<div className={`font-mono whitespace-pre overflow-hidden ${className}`}>
				No frames loaded
			</div>
		);
	}

	return (
		<div
			className={`relative font-mono whitespace-pre overflow-hidden leading-none ${className}`}
			style={{ fontSize: size }}
		>
			<div
				className={`whitespace-pre ${colorOverlay ? "text-gradient-accent" : ""}`}
			>
				{frames[currentFrame]}
			</div>
		</div>
	);
}
