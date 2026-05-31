import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { Dashboard } from "./components/Dashboard";
import { FaceTraining } from "./components/FaceTraining";
import { PhotoOrganization } from "./components/PhotoOrganization";
import { LocationGallery } from "./components/LocationGallery";
import { EventGallery } from "./components/EventGallery";
import { UnidentifiedPhotos } from "./components/UnidentifiedPhotos";
import { Settings } from "./components/Settings";
import { Deduplicator } from "./components/Deduplicator"; 

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: Dashboard },
      { path: "train", Component: FaceTraining },
      { path: "organize", Component: PhotoOrganization },
      { path: "deduplicate", Component: Deduplicator }, 
      { path: "locations", Component: LocationGallery },
      { path: "events", Component: EventGallery },
      { path: "unidentified", Component: UnidentifiedPhotos },
      { path: "settings", Component: Settings },
    ],
  },
], {
  future: {
    v7_relativeSplatPath: true,
    v7_fetcherPersist: true,
    v7_normalizeFormMethod: true,
    v7_partialHydration: true,
    v7_skipActionErrorRevalidation: true,
  }
});