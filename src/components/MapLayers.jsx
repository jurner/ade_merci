import { DataFilterExtension } from "@deck.gl/extensions";
import settings from "../data/settings.json";
import sp from "../data/staypoints.json";
import tpl from "../data/triplegs.json";
import flights from "../data/flights.json";
import place_names from "../data/place_names.json";
import attractions from "../data/attractions.json";

import {
  TripsLayer,
  IconLayer,
  PathLayer,
  ArcLayer,
  TextLayer,
} from "@deck.gl/layers";

const createLayers = (
  time,
  tpl,
  sp,
  flights,
  place_names,
  attractions,
  settings
) => {
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
      data: sp,
      // iconAtlas and iconMapping should not be provided
      // getIcon return an object which contains url to fetch icon of each data point
      getIcon: (d) => ({
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
      filterRange: [0, time],
      getLineColor: (d) => [0, 0, 0],
      extensions: [new DataFilterExtension({ filterSize: 1 })],
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
      sizeUnits: "meters",
      getSize: 600,
      getAngle: 0,
      getTextAnchor: "middle",
      getAlignmentBaseline: "center",
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
  return layers;
};
export default createLayers;
