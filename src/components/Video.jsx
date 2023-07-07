import React, { useRef, useEffect } from "react";

const Video = ({ week }) => {
  const videoRef = useRef(null);

  useEffect(() => {
    const loadVideo = async () => {
      try {
        const videoModule = await import(`../data/1se/${week}w.mp4`);
        const videoPath = videoModule.default;
        videoRef.current.src = videoPath;
        videoRef.current.load();
      } catch (error) {
        console.error("Error loading video:", error);
      }
    };

    loadVideo();
  }, [week]);

  return (
    <>
      <video
        ref={videoRef}
        width="100%"
        height="auto"
        autoplay
        controls
        loop
        muted
      >
        <source type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </>
  );
};

export default Video;
