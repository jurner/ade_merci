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
//import createLayers from "./MapLayers"; // Import the createLayers function

import camera from "../data/camera.json";
import flights from "../data/flights.json";
import tpl from "../data/triplegs.json";
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

function getNextActivity(number, data) {
  for (let i = 0; i < data.length; i++) {
    if (number >= data[i].started && number < data[i].finished) {
      return data[i];
    }
  }
  console.log("Next activity not found");
  return {};
}

const MapView = () => {
  const [time, setTime] = useState(settings.start_time);
  const [animation] = useState({});
  const week = useStore((state) => state.week);
  const speed = useStore((state) => state.speed);

  var started = weekly_data[settings.start_week.toString()].started;
  var finished = weekly_data[settings.start_week.toString()].finished;
  const [tsBounds, setTsBounds] = useState([started, finished]);

  const [minutes, setMinutes] = useState(1);
  const [hours, setHours] = useState(1);
  const [loopLength, setLoopLength] = useState(finished);
  const [currentActivity, setCurrentActivity] = useState({});
  const [initialViewState, setInitialViewState] = useState(
    settings.initial_view_state
  );

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

  const flyToCoord = useCallback((c) => {
    setInitialViewState({
      longitude: c.go_to_coord[0],
      latitude: c.go_to_coord[1],
      zoom: c.zoom,
      pitch: 45,
      bearing: 0,
      transitionDuration: c.duration / 1.5,
      transitionInterpolator: new FlyToInterpolator({ curve: c.curve }),
    });
  }, []);

  useEffect(() => {
    animation.id = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(animation.id);
  }, [animation, loopLength]);

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
      if (c.timestamp - speed <= time && c.timestamp + speed >= time) {
        flyToCoord(c);
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

  const layers = [
    new TripsLayer({
      id: "trips",
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
    new IconLayer({
      id: "icon-layer",
      data: sp2,
      extruded: true,
      // iconAtlas and iconMapping should not be provided
      // getIcon return an object which contains url to fetch icon of each data point
      getIcon: (d) => ({
        // TODO fix path url
        url: d.icon,
        width: 50,
        height: 50,
        anchorY: 50,
      }),
      // icon size is based on data point's contributions, between 2 - 25
      getSize: (d) => 2,
      pickable: true,
      sizeScale: 15,
      getPosition: (d) => d.coords,
      getColor: (d) => [255, 140, 0],
      getFilterValue: (d) => d.started,
      //filterRange: [0, time],
      getLineColor: (d) => [0, 0, 0],
      //extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
    new PathLayer({
      id: "path-layer",
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
    new ArcLayer({
      id: "arc-layer",
      data: flights,
      pickable: true,
      getWidth: 2,
      opacity: 0.5,
      getSourcePosition: (d) => d.path[0],
      getTargetPosition: (d) => d.path[d.path.length - 1],
      getSourceColor: (d) => settings.trailColor,
      getTargetColor: (d) => settings.trailColor,
      getFilterValue: (d) => d.timestamps[0],
      filterRange: [0, time],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
    new TextLayer({
      id: "text-layer",
      data: place_names,
      pickable: true,
      getPosition: (d) => d.coords,
      getText: (d) => d.name,
      fontFamily: "DIN Pro Medium",
      //sizeUnits: "meters",
      getSize: 25,
      getAngle: 0,
      getTextAnchor: "middle",
      getAlignmentBaseline: "center",
      extruded: true,
      // background: true,
      // backgroundPadding: [1, 1],
      // getBackgroundColor:[255, 255, 255,50],
      fontSettings: {
        sdf: true,
      },
      getTextOutline: true,
      getTextOutlineWidth: 10000000,
      getTextOutlineColor: [255, 255, 255],
      getTextOutline: () => ({
        color: [255, 255, 255, 255],
        size: 100,
        blur: 2,
      }),
      getFilterValue: (d) => d.started,
      filterRange: [0, time + 3],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
    new TextLayer({
      id: "text-layer",
      data: place_names,
      pickable: true,
      getPosition: (d) => d.coords,
      getText: (d) => d.name,
      fontFamily: "DIN Pro Medium",
      getSize: 70,
      getAngle: 0,
      getTextAnchor: "middle",
      getAlignmentBaseline: "center",
      extruded: true,
      fontSettings: {
        sdf: true,
      },
      // TODO make outlines working
      getTextOutline: true,
      getTextOutlineWidth: 10000000,
      getTextOutlineColor: [255, 255, 255],
      getTextOutline: () => ({
        color: [255, 255, 255, 255],
        size: 100,
        blur: 2,
      }),
      // background: true,
      // backgroundPadding: [4, 4],
      // getBackgroundColor:[255, 255, 255],
      getFilterValue: (d) => d.started,
      filterRange: [time, time + 3 * 3600],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
    new TextLayer({
      id: "text-layer",
      data: attractions,
      pickable: true,
      getPosition: (d) => d.coords,
      getText: (d) => d.name,
      fontFamily: "DIN Pro Medium",
      sizeUnits: "meters",
      getSize: 800,
      getAngle: 0,
      getTextAnchor: "middle",
      getAlignmentBaseline: "center",
      getTextOutline: true,
      getTextOutlineWidth: 10000000,
      getFilterValue: (d) => d.started,
      filterRange: [time - 12 * 3600, time],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
    }),
  ];
  // const layers = createLayers(
  //   time,
  //   tpl,
  //   sp,
  //   flights,
  //   place_names,
  //   attractions,
  //   settings
  // ); // Use createLayers to create the layers

  return (
    <>
      <Container>
        <Row>
          <Col sm={8}>
            <DeckGL
              layers={layers}
              initialViewState={initialViewState}
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
