import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { ReactNode } from "react"
// The react-bpmn library has a bug that prevents it from working out of the box.
// We need to import the component directly from the source file.
// @ts-ignore
import BpmnJS from "react-bpmn/lib/Viewer"

interface State {
  xml: string
}

class BPMN_to_Image extends StreamlitComponentBase<State> {
  public state = { xml: this.props.args["xml"] }

  // This function is called automatically once the diagram is loaded
  private handleLoad = async ({ viewer }: any) => {
    if (viewer) {
      try {
        // Export the diagram to SVG
        const { svg } = await viewer.saveSVG();
        // Send the SVG string back to the Streamlit Python backend
        Streamlit.setComponentValue(svg);
      } catch (err) {
        console.error("Failed to save SVG", err);
      }
      Streamlit.setComponentReady();
    }
  }

  public render = (): ReactNode => {
    // The component is rendered in a hidden div so the user doesn't see it.
    // It does its work in the background.
    return (
      <div style={{ height: 0, overflow: 'hidden' }}>
        <BpmnJS
          url={this.state.xml}
          onLoad={this.handleLoad}
        />
      </div>
    )
  }
}

export default withStreamlitConnection(BPMN_to_Image)
