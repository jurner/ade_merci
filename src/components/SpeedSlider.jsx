import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import useStore from "../appStore";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faGaugeSimple } from "@fortawesome/free-solid-svg-icons";
const SpeedSlider = () => {
  const speed = useStore((state) => state.speed);
  const setSpeed = useStore((state) => state.setSpeed);

  const handleSpeedChange = (event) => {
    const newSpeed = parseFloat(event.target.value);
    setSpeed(newSpeed);
  };

  const containerStyle = {
    marginLeft: "20px",
    marginRight: "20px",
  };
  return (
    <>
      <div style={containerStyle} className="d-flex align-items-center">
        <FontAwesomeIcon icon={faGaugeSimple} />{" "}
        <input
          type="range"
          min="50"
          max="200"
          step="5"
          value={speed}
          onChange={handleSpeedChange}
          className="form-range"
        />
      </div>
      <div>
        <p>Speed: {speed / 100}x</p>
      </div>
    </>
  );
};

export default SpeedSlider;
