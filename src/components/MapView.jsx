import { useCallback, useState, useEffect } from "react";
import Map from "react-map-gl";
import DeckGL from "@deck.gl/react";
import { ArcLayer, PathLayer, IconLayer, TextLayer } from "@deck.gl/layers";
import { TripsLayer } from "@deck.gl/geo-layers";
import { FlyToInterpolator } from "deck.gl";
import { DataFilterExtension } from "@deck.gl/extensions";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import "bootstrap/dist/css/bootstrap.min.css";
import PostCard from "./PostCard";
import useStore from "../appStore";
import FlipClock from "./FlipClock";

import camera from "../data/camera.json";
import flights from "../data/flights.json";
import tpl from "../data/tpl.json";
import weekly_data from "../data/weekly_data.json";
import sp2 from "../data/sp.json";
import place_names from "../data/place_names.json";
import attractions from "../data/attractions.json";
import settings from "../data/settings.json";
import no_share from "../private.json";

function getHourFromTimestamp(timestamp) {
  // Convert the timestamp to milliseconds
  const milliseconds = timestamp * 1000;

  // Create a new Date object
  const date = new Date(milliseconds);

  // Get the hour from the Date object
  const hour = date.getHours();
  return hour;
}

function getMinuteFromTimestamp(timestamp) {
  // Convert the timestamp to milliseconds
  const milliseconds = timestamp * 1000;

  // Create a new Date object
  const date = new Date(milliseconds);

  // Get the hour from the Date object
  const minute = date.getMinutes();

  return minute;
}

const MapView = () => {
  const [time, setTime] = useState(settings.start_time);
  const [animation] = useState({});
  const week = useStore((state) => state.week);
  const speed = useStore((state) => state.speed);
  const setSpeed = useStore((state) => state.setSpeed);

  var started = weekly_data[settings.start_week.toString()].started;
  var finished = weekly_data[settings.start_week.toString()].finished;
  const [tsBounds, setTsBounds] = useState([started, finished]);

  const [minutes, setMinutes] = useState(1);
  const [hours, setHours] = useState(1);
  const [loopLength, setLoopLength] = useState(finished);
  const [currentActivity, setCurrentActivity] = useState({});
  const [viewState, setViewState] = useState(settings.initial_view_state);
  const running = useStore((state) => state.running);

  const animate = () => {
    setTime((t) => {
      if (t >= loopLength - speed) {
        //return tsBounds[0];
        return loopLength;
      } else {
        return t + speed;
      }
    });

    animation.id = window.requestAnimationFrame(animate);
  };
  function getNextActivity(number, data) {
    for (let i = 0; i < data.length; i++) {
      if (number >= data[i].started && number < data[i].finished) {
        return data[i];
      }
    }
    return {};
  }
  const calcNextViewState = (c, t) => {
    let time_since_start = t - c.start_dt;
    let perc_finished = time_since_start / c.duration;
    let lon = c.start_lon + (c.end_lon - c.start_lon) * perc_finished;
    let lat = c.start_lat + (c.end_lat - c.start_lat) * perc_finished;
    let zoom = c.start_zoom + (c.end_zoom - c.start_zoom) * perc_finished;
    if (c.speed != speed) {
      setSpeed(c.speed);
    }

    setViewState((prevState) => ({
      ...prevState,
      longitude: lon,
      latitude: lat,
      zoom: zoom,
    }));
  };

  const flyToCoord = useCallback((c) => {
    setViewState({
      longitude: c.go_to_coord[0],
      latitude: c.go_to_coord[1],
      zoom: c.zoom,
      pitch: 45,
      bearing: 0,
      //transitionDuration: c.duration / 1.5,
      //transitionInterpolator: new FlyToInterpolator({ curve: c.curve }),
    });
  }, []);

  // useEffect(() => {
  //   animation.id = window.requestAnimationFrame(animate);
  //   return () => window.cancelAnimationFrame(animation.id);
  // }, [animation, loopLength]);

  // function svgToDataURL(svg) {
  //   return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(bed)}`;
  // }

  function createSVGIcon(name, color, halo) {
    return `\
    <svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">
      <text x="300" y="100" fill="${color}" text-anchor="center" stroke="${halo}" stroke-width="7" alignment-baseline="middle" font-size="50">${name}</text>
      <text x="300" y="100" fill="${color}" text-anchor="center" alignment-baseline="middle" font-size="50">${name}</text>
    </svg>`;
  }

  function svgToDataURL(svg) {
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  }

  useEffect(() => {
    var started = weekly_data[week.toString()].started;
    var finished = weekly_data[week.toString()].finished;
    setTsBounds([started, finished]);
  }, [week]);

  useEffect(() => {
    setLoopLength(tsBounds[1]);
    setTime(tsBounds[0]);
  }, [tsBounds]);

  useEffect(() => {
    camera.forEach((c) => {
      if (c.start_dt <= time && c.end_dt >= time) {
        calcNextViewState(c, time);
      }
    });

    if (Object.keys(currentActivity).length === 0) {
      setCurrentActivity(
        getNextActivity(time, JSON.parse(weekly_data[week.toString()].data))
      );
    } else {
      let activity = getNextActivity(
        time,
        JSON.parse(weekly_data[week.toString()].data)
      );
      if (currentActivity.index != activity.index) {
        setCurrentActivity(
          getNextActivity(time, JSON.parse(weekly_data[week.toString()].data))
        );
      }
    }
    if (hours !== getHourFromTimestamp(time)) {
      setHours(getHourFromTimestamp(time));
    }
    let currentMinutes = Math.floor(getMinuteFromTimestamp(time) / 11) * 11;
    if (minutes !== currentMinutes) {
      setMinutes(currentMinutes);
    }
  }, [time]);

  useEffect(() => {
    //stop animation
    if (!running) {
      window.cancelAnimationFrame(animate.id);
      return;
    }
    // start animation
    animation.id = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(animation.id);
  }, [running, loopLength]);

  const layers = [
    new TripsLayer({
      id: 0,
      data: tpl,
      getPath: (d) => d.path,
      getTimestamps: (d) => d.timestamps,
      getColor: (d) =>
        d.vendor === 0 ? settings.trailColor : settings.trailColor,
      //opacity: 0,
      widthMinPixels: 8,
      rounded: true,
      trailLength: settings.trailLength,
      currentTime: time,
      shadowEnabled: false,
    }),

    new PathLayer({
      id: 1,
      data: tpl,
      pickable: true,
      widthScale: 2,
      widthMinPixels: 3,
      opacity: 0.6,
      getPath: (d) => d.path,
      getColor: (d) => settings.trailColor,
      getWidth: (d) => 4,
      getFilterValue: (d) => d.timestamps[d.timestamps.length - 1],
      filterRange: [0, time],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
    new IconLayer({
      id: 2,
      data: attractions,
      extruded: true,
      getIcon: (d) => ({
        url: svgToDataURL(createSVGIcon(d.name, "#8a502e", "white")),
        width: 400,
        height: 300,
      }),
      getSize: (d) => d.size,
      pickable: false,
      sizeScale: 75,
      getPosition: (d) => d.coords,
      getFilterValue: (d) => d.started,
      filterRange: [time - 2 * 3600, time + 168 * 3600],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),

    // new IconLayer({
    //   id: 3,
    //   data: place_names,
    //   extruded: true,
    //   getIcon: (d) => ({
    //     url: svgToDataURL(createSVGIcon(d.name, "#8a502e", "white")),
    //     width: 400,
    //     height: 300,
    //   }),
    //   getSize: (d) => 2,
    //   pickable: false,
    //   sizeScale: 75,
    //   getPosition: (d) => d.coords,
    //   getFilterValue: (d) => d.started,
    //   filterRange: [0, time],
    //   extensions: [new DataFilterExtension({ filterSize: 1 })],
    // }),
    // new IconLayer({
    //   id: 3,
    //   data: place_names,
    //   extruded: true,
    //   getIcon: (d) => ({
    //     url: svgToDataURL(createSVGIcon(d.name, "#8a502e", "white")),
    //     width: 400,
    //     height: 300,
    //   }),
    //   getSize: (d) => d.size,
    //   pickable: false,
    //   sizeScale: 75,
    //   getPosition: (d) => d.coords,
    //   getFilterValue: (d) => d.started,
    //   filterRange: [0, time],
    //   extensions: [new DataFilterExtension({ filterSize: 1 })],
    // }),
    // new IconLayer({
    //   id: 5,
    //   sp2,
    //   pickable: true,
    //   getIcon: (d) => ({
    //     url: d.icon,
    //     width: 128,
    //     height: 128,
    //     anchorY: 128,
    //     mask: true,
    //   }),
    //   getPosition: (d) => d.coords,
    //   sizeScale: 1000,
    //   getSize: 1000,
    // }),
    new ArcLayer({
      id: 4,
      data: flights,
      pickable: true,
      getWidth: 2.5,
      opacity: 0.8,
      getHeight: (d) => 0.7,
      getSourcePosition: (d) => d.path[0],
      getTargetPosition: (d) => d.path[d.path.length - 1],
      getSourceColor: (d) => settings.flightColor,
      getTargetColor: (d) => settings.flightColor,
      getFilterValue: (d) => d.timestamps[0],
      filterRange: [0, time],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
  ];

  return (
    <>
      <Container>
        <Row>
          <Col sm={8}>
            <DeckGL
              layers={layers}
              initialViewState={viewState}
              controller={true}
            >
              <div
              // style={{ color: "white", position: "absolute", paddingLeft: "40px" }}
              >
                <FlipClock hours={hours} minutes={minutes}></FlipClock>
              </div>
              <Map
                mapboxAccessToken={no_share.mapboxToken}
                reuseMaps
                mapStyle={settings.mapStyle}
                //preventStyleDiffing={true}
              />
            </DeckGL>
          </Col>
          <Col sm={4}>
            <div className="mapCardContainer">
              <PostCard week={week} data={currentActivity}></PostCard>
            </div>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default MapView;
