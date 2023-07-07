import React, { useRef, useState, useEffect } from "react";
import Card from "react-bootstrap/Card";
import "bootstrap/dist/css/bootstrap.min.css";
import video from "../data/1se/1w.mp4";
import useStore from "../appStore";
import SpeedSlider from "./SpeedSlider";
import Video from "./Video";
import Distance from "./Distance";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faChevronRight,
  faChevronLeft,
  faPlay,
  faPause,
} from "@fortawesome/free-solid-svg-icons";

import car from "../assets/car.gif";
import bus from "../assets/bus.gif";
import bicycle from "../assets/cycling.gif";
import scooter from "../assets/scooter.gif";
import train from "../assets/train.gif";
import walk from "../assets/walk.gif";
import airplane from "../assets/airplane.gif";
import boat from "../assets/galleon.gif";
import pin from "../assets/pin.gif";

import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

function getLogo(activity) {
  let type = activity.type;
  if (type === null) {
    return pin;
  }

  switch (type) {
    case "FLYING":
      return airplane;
    case "MOTORCYCLING":
      return scooter;
    case "CYCLING":
      return bicycle;
    case "WALKING":
      return walk;
    case "IN_BUS":
      return bus;
    case "IN_TRAIN":
      return train;
    case "BOATING":
      return boat;
    case "IN_SUBWAY":
      return train;
    case "IN_FERRY":
      return boat;
    case "IN_TAXI":
      return car;
    case "IN_PASSENGER_VEHICLE":
      return car;
    default:
      return pin;
  }
}

const getTime = (dateStr) => {
  const date = new Date(dateStr);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const formattedTime = `${hours}:${minutes}`;
  return formattedTime;
};

const getDate = (data) => {
  if (data === null) {
    return "";
  }
  const date = new Date(data.started_at);
  const options = { weekday: "short", day: "2-digit", month: "2-digit" };
  const dayName = date.toLocaleDateString("de-DE", options).split(",")[0];
  const formattedDate = date.toLocaleString("de-DE", options).split(",")[1];
  return `${dayName} ${formattedDate}`;
};

function getEntryInfo(currentActivity) {
  if (currentActivity === null) {
    return <p></p>;
  } else {
    let startTime = getTime(currentActivity.started_at);
    let finishTime = getTime(currentActivity.finished_at);
    let title = "";
    if (!currentActivity.type) {
      return <></>;
    }
    if (currentActivity.type.includes("[")) {
      title = currentActivity.name;
    } else {
      title = currentActivity.type;
    }
    return (
      <div id="entryInfo">
        <h5>{title}</h5>
        <p>
          {startTime} - {finishTime}
        </p>
      </div>
    );
  }
}

const PostCard = ({ week, data }) => {
  const setWeek = useStore((state) => state.setWeek);
  const setRunning = useStore((state) => state.setRunning);
  const running = useStore((state) => state.running);

  const incrementWeek = () => {
    let new_val = week + 1;
    setWeek(new_val);
  };
  const decrementWeek = () => {
    let new_val = week - 1;
    setWeek(new_val);
  };

  const toggleRunning = () => {
    setRunning(!running);
  };

  return (
    <>
      <Card style={{ height: "90vh" }} className="mapCard">
        <Video week={week}></Video>
        <Card.Body>
          <Row>
            <Col sm={3}>
              <button
                disabled={week === 0}
                onClick={decrementWeek}
                style={{
                  backgroundColor: "#2a9d8f",
                  color: "white",
                  width: "40px",
                  height: "40px",
                }}
                className="btn rounded-circle"
              >
                <FontAwesomeIcon icon={faChevronLeft} />
              </button>
            </Col>
            <Col sm={6}>
              <Row>
                <h4>Woche {week}</h4>
              </Row>
              <Row>
                <p>{getDate(data)}</p>
              </Row>
            </Col>
            <Col sm={3}>
              <button
                disabled={week === 100}
                onClick={incrementWeek}
                style={{
                  backgroundColor: "#2a9d8f",
                  color: "white",
                  width: "40px",
                  height: "40px",
                }}
                className="btn rounded-circle"
              >
                <FontAwesomeIcon icon={faChevronRight} />
              </button>
            </Col>
            <hr></hr>
            <Col sm={4}>
              <img
                style={{ width: "100%" }}
                src={getLogo(data)}
                alt="loading..."
              />
            </Col>
            <Col sm={8}>{getEntryInfo(data)}</Col>
          </Row>
          <SpeedSlider></SpeedSlider>
          <button
            disabled={week === 14}
            onClick={toggleRunning}
            style={{
              backgroundColor: "#2a9d8f",
              color: "white",
              height: "40px",
            }}
            className="btn"
          >
            {running ? (
              <FontAwesomeIcon icon={faPause} />
            ) : (
              <FontAwesomeIcon icon={faPlay} />
            )}
          </button>
          <Distance data={data}></Distance>
        </Card.Body>
      </Card>
    </>

    // <div id={week}>
    //       <Container>
    //         <Row>
    //           <Col sm={12}>
    //             <h2>Woche {week}</h2>

    //           </Col>
    //           <Col sm={6}>
    //             <img style={{'width':"100%"}} src={getLogo(data)} alt="loading..." />
    //           </Col>
    //           <Col sm={6}>
    //             {getEntryInfo(data)}
    //           </Col>
    //         </Row>
    //       </Container>
    // </div>
  );
};

export default PostCard;
