import "./FlipClock.css";

import React, { useState, useEffect } from "react";

const AnimatedCard = ({ animation, digit }) => {
  return (
    <div className={`flipCard ${animation}`}>
      <span>{digit}</span>
    </div>
  );
};

const StaticCard = ({ position, digit }) => {
  return (
    <div className={position}>
      <span>{digit}</span>
    </div>
  );
};

const FlipUnitContainer = ({ digit, shuffle }) => {
  const [digits, setDigits] = useState([digit, digit - 1]);

  useEffect(() => {
    setDigits([digit, digits[0]]);
  }, [digit]);

  let [currentDigit, previousDigit] = digits;

  if (currentDigit < 10) {
    currentDigit = `0${currentDigit}`;
  }
  if (previousDigit < 10) {
    previousDigit = `0${previousDigit}`;
  }

  const digit1 = shuffle ? previousDigit : currentDigit;
  const digit2 = !shuffle ? previousDigit : currentDigit;

  const animation1 = shuffle ? "fold" : "unfold";
  const animation2 = !shuffle ? "fold" : "unfold";

  return (
    <div className="flipUnitContainer">
      <StaticCard position="upperCard" digit={currentDigit} />
      <StaticCard position="lowerCard" digit={previousDigit} />
      <AnimatedCard digit={digit1} animation={animation1} />
      <AnimatedCard digit={digit2} animation={animation2} />
    </div>
  );
};

const FlipClock = ({ hours, minutes }) => {
  const [hoursState, setHours] = useState(hours);
  const [hoursShuffle, setHoursShuffle] = useState(true);
  const [minutesState, setMinutes] = useState(minutes);
  const [minutesShuffle, setMinutesShuffle] = useState(true);

  useEffect(() => {
    if (hours != hoursState) {
      setHours(hours);
      setHoursShuffle(!hoursShuffle);
    }
  }, [hours, hoursState, hoursShuffle]);

  useEffect(() => {
    if (minutes != minutesState) {
      setMinutes(minutes);
      setMinutesShuffle(!minutesShuffle);
    }
  }, [minutes, minutesState, minutesShuffle]);

  return (
    <div className="flipClock">
      <FlipUnitContainer digit={hoursState} shuffle={hoursShuffle} />
      <FlipUnitContainer digit={minutesState} shuffle={minutesShuffle} />
    </div>
  );
};

export default FlipClock;
