import React, { useState, useRef, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

const Distance = ({ data }) => {
  const [dist, setDist] = useState(null);

  useEffect(() => {
    if (data.type) {
      setDist(data.distance.toString());
    } else {
      setDist(null);
    }
  }, [data]);

  return <>{dist !== null ? <h1>{dist}</h1> : <h6>no data</h6>}</>;
};

export default Distance;
