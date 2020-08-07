import { dataFrameToArrayOfDicts } from "lib/dataFrameProto"
import DeckGL, {
  ArcLayer,
  GridLayer,
  HexagonLayer,
  LineLayer,
  PointCloudLayer,
  ScatterplotLayer,
  ScreenGridLayer,
  TextLayer,
  // @ts-ignore
} from "deck.gl"
/**
 * Defines default getters for columns.
 */
const Defaults = {
  ArcLayer: {
    getSourceColor: getSourceColorFromSourceColorRGBAColumns,
    getTargetColor: getTargetColorFromTargetColorRGBAColumns,
    getSourcePosition: getPositionFromLatLonColumns,
    getTargetPosition: getTargetPositionFromLatLonColumn,
  },

  // GeoJsonLayer: TODO. Data needs to be sent as JSON, not dataframe.

  GridLayer: {
    getPosition: getPositionFromLatLonColumns,
  },

  HexagonLayer: {
    getPosition: getPositionFromLatLonColumns,
  },

  LineLayer: {
    getSourcePosition: getPositionFromLatLonColumns,
    getTargetPosition: getTargetPositionFromLatLonColumn,
  },

  // IconLayer: TODO
  // PathLayer: TODO

  PointCloudLayer: {
    getColor: getColorFromColorRGBAColumns,
    getPosition: getPositionFromPositionXYZColumns,
    getNormal: getNormalFromNormalXYZColumns,
  },

  // PolygonLayer: TODO

  ScatterplotLayer: {
    getColor: getColorFromColorRGBAColumns,
    getPosition: getPositionFromLatLonColumns,
    getRadius: (d: any) => fallback(d.radius, 100),
  },

  ScreenGridLayer: {
    getPosition: getPositionFromLatLonColumns,
    getWeight: (d: any) => d.weight,
  },

  TextLayer: {
    getColor: getColorFromColorRGBAColumns,
    getPixelOffset: (d: any) => [
      fallback(d.pixelOffsetX, 0),
      fallback(d.pixelOffsetY, 0),
    ],
    getPosition: getPositionFromLatLonColumns,
    getAlignmentBaseline: "bottom",
  },
}

export function buildLayer(layer: any): any {
  const data = dataFrameToArrayOfDicts(layer.get("data"))
  const spec = JSON.parse(layer.get("spec"))

  const type = spec.type ? spec.type.toLowerCase() : ""
  delete spec.type

  parseGetters(type, spec)

  switch (type) {
    case "arclayer":
      return new ArcLayer({
        data,
        ...Defaults.ArcLayer,
        ...spec,
      })

    case "gridlayer":
      return new GridLayer({
        data,
        ...Defaults.GridLayer,
        ...spec,
      })

    case "hexagonlayer":
      return new HexagonLayer({
        data,
        ...Defaults.HexagonLayer,
        ...spec,
      })

    case "linelayer":
      return new LineLayer({
        data,
        ...Defaults.LineLayer,
        ...spec,
      })

    case "pointcloudlayer":
      return new PointCloudLayer({
        data,
        ...Defaults.PointCloudLayer,
        ...spec,
      })

    case "scatterplotlayer":
      return new ScatterplotLayer({
        data,
        ...Defaults.ScatterplotLayer,
        ...spec,
      })

    case "screengridlayer":
      return new ScreenGridLayer({
        data,
        ...Defaults.ScreenGridLayer,
        ...spec,
      })

    case "textlayer":
      return new TextLayer({
        data,
        ...Defaults.TextLayer,
        ...spec,
      })

    default:
      throw new Error(`Unsupported layer type "${type}"`)
  }
}

// Set of DeckGL Layers that take a getPosition argument. We'll allow users to
// specify position columns via getLatitude and getLongitude instead.
const POSITION_LAYER_TYPES = new Set([
  "gridlayer",
  "hexagonlayer",
  "scatterplotlayer",
  "screengridlayer",
  "textlayer",
])

// Set of DeckGL Layers that take a getSourcePosition/getTargetPosition
// arguments.  We'll allow users to specify position columns via
// getLatitude/getTargetLatitude and getLongitude/getTargetLongitude instead.
const SOURCE_TARGET_POSITION_LAYER_TYPES = new Set(["arclayer", "linelayer"])

// Set of DeckGL Layers that take a getColor argument. We'll allow users to
// specify color columns via getColorR, getColorB, ggetColorG and getColorA instead.
const COLOR_LAYER_TYPES = new Set([
  "pointcloudlayer",
  "scatterplotlayer",
  "textlayer",
])

// Set of DeckGL Layers that take a getSourceColor/getTargetColor argument.
// We'll allow users to specify color columns via getColorR/getTargetColorR,
// getColorG/getTargetColorG, etc. instead
const SOURCE_TARGET_COLOR_LAYER_TYPES = new Set(["arclayer"])

/**
 * Take a short "map style" string and convert to the full URL for the style.
 * (And it only does this if the input string is not already a URL.)
 *
 * See https://www.mapbox.com/maps/ or https://www.mapbox.com/mapbox-gl-js/api/
 */
export function getStyleUrl(styleStr = "light-v9"): string {
  if (
    styleStr.startsWith("http://") ||
    styleStr.startsWith("https://") ||
    styleStr.startsWith("mapbox://")
  ) {
    return styleStr
  }

  return `mapbox://styles/mapbox/${styleStr}`
}

/**
 * Returns the first non-null/non-undefined argument.
 *
 * Usage:
 *   fallback(value, fallbackValue)
 *
 * Accepts infinitely many arguments:
 *   fallback(value, fallback1, fallback2, fallback3)
 */
function fallback(...args: any[]): any | null {
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] != null) {
      return args[i]
    }
  }
  return null
}

/* Define a bunch of getters */

function getPositionFromLatLonColumns(d: any): any[] {
  return [fallback(d.longitude, d.lon), fallback(d.latitude, d.lat)]
}

function getTargetPositionFromLatLonColumn(d: any): any[] {
  return [fallback(d.longitude2, d.lon2), fallback(d.latitude2, d.lat2)]
}

function getPositionFromPositionXYZColumns(d: any): any[] {
  return [
    fallback(d.longitude, d.lon, d.positionX, d.x),
    fallback(d.latitude, d.lat, d.positionY, d.y),
    fallback(d.latitude, d.lat, d.positionZ, d.z),
  ]
}

function getNormalFromNormalXYZColumns(d: any): number[] {
  return [d.normalX, d.normalY, d.normalZ]
}

const DEFAULT_COLOR = [200, 30, 0, 160]

function getColorFromColorRGBAColumns(d: any): number[] {
  return d.colorR && d.colorG && d.colorB
    ? [d.colorR, d.colorG, d.colorB, d.colorA == null ? 255 : d.colorA]
    : DEFAULT_COLOR
}

function getSourceColorFromSourceColorRGBAColumns(d: any): number[] {
  return d.colorR && d.colorG && d.colorB
    ? [d.colorR, d.colorG, d.colorB, d.colorA == null ? 255 : d.colorA]
    : DEFAULT_COLOR
}

function getTargetColorFromTargetColorRGBAColumns(d: any): number[] {
  return d.targetColorR && d.targetColorG && d.targetColorB
    ? [
        d.targetColorR,
        d.targetColorG,
        d.targetColorB,
        d.targetColorA == null ? 255 : d.targetColorA,
      ]
    : DEFAULT_COLOR
}

function parseGetters(type: any, spec: any): void {
  // If this is a layer that accepts a getPosition argument, build that
  // argument from getLatiude and getLongitude.
  if (
    POSITION_LAYER_TYPES.has(type) &&
    spec.getLatitude &&
    spec.getLongitude
  ) {
    const latField = spec.getLatitude
    const lonField = spec.getLongitude
    spec.getPosition = (d: any) => [d[lonField], d[latField]]
  }

  // Same as the above, but for getSourcePosition/getTargetPosition.
  if (
    SOURCE_TARGET_POSITION_LAYER_TYPES.has(type) &&
    spec.getLatitude &&
    spec.getLongitude &&
    spec.getTargetLatitude &&
    spec.getTargetLongitude
  ) {
    const latField = spec.getLatitude
    const lonField = spec.getLongitude
    const latField2 = spec.getTargetLatitude
    const lonField2 = spec.getTargetLongitude
    spec.getSourcePosition = (d: any) => [d[lonField], d[latField]]
    spec.getTargetPosition = (d: any) => [d[lonField2], d[latField2]]
  }

  // If this is a layer that accepts a getColor argument, build that
  // argument from getColorR, getColorG and getColorB.
  if (
    COLOR_LAYER_TYPES.has(type) &&
    spec.getColorR &&
    spec.getColorG &&
    spec.getColorB
  ) {
    const rField = spec.getColorR
    const gField = spec.getColorG
    const bField = spec.getColorB
    const aField = spec.getColorA
    spec.getColor = (d: any) => [d[rField], d[gField], d[bField], d[aField]]
  }

  // Same as the above, but for getSourceColor/getTargetColor.
  if (
    SOURCE_TARGET_COLOR_LAYER_TYPES.has(type) &&
    spec.getColorR &&
    spec.getColorG &&
    spec.getColorB &&
    spec.getTargetColorR &&
    spec.getTargetColorG &&
    spec.getTargetColorB
  ) {
    const rField = spec.getColorR
    const gField = spec.getColorG
    const bField = spec.getColorB
    const aField = spec.getColorA
    const rField2 = spec.getTargetColorR
    const gField2 = spec.getTargetColorG
    const bField2 = spec.getTargetColorB
    const aField2 = spec.getTargetColorA
    spec.getSourceColor = (d: any) => [
      d[rField],
      d[gField],
      d[bField],
      d[aField],
    ]
    spec.getTargetColor = (d: any) => [
      d[rField2],
      d[gField2],
      d[bField2],
      d[aField2],
    ]
  }

  Object.keys(spec).forEach(key => {
    if (!key.startsWith("get")) {
      return
    }
    const v = spec[key]
    if (typeof v === "function") {
      // Leave functions untouched.
    } else if (typeof v === "string") {
      spec[key] = (d: any) => d[v] // Make getters from strings.
    } else {
      spec[key] = () => v // Make constant function otherwise.
    }
  })
}
