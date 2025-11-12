import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import React, { useEffect, useRef } from "react";
import BpmnJS from 'bpmn-js/lib/Modeler';

interface ComponentProps {
  args: {
    xml: string;
  }
}

function BPMN2Image(props: ComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Effect 1: Tell Streamlit we are ready.
  // The empty dependency array [] means this runs only ONCE when the component first mounts.
  useEffect(() => {
    Streamlit.setComponentReady();
  }, []);

  // Effect 2: Do the conversion work.
  // This runs whenever the `xml` prop changes.
  useEffect(() => {
    const { xml } = props.args;
    const container = containerRef.current;

    // Don't do anything if we don't have the necessary ingredients.
    if (!container || !xml) {
      return;
    }

    const bpmnViewer = new BpmnJS({ container: container });
    
    const convertXmlToSvg = async () => {
      try {
        console.log("Attempting to import BPMN XML...");
        await bpmnViewer.importXML(xml);
        console.log("XML imported successfully. Attempting to save SVG...");

        const { svg } = await bpmnViewer.saveSVG();
        console.log("SVG successfully generated!");

        // Send the SVG string back to Python.
        Streamlit.setComponentValue(svg);

      } catch (err) {
        console.error("BPMN conversion failed:", err);
        // Optional: send back an error message.
        Streamlit.setComponentValue({ error: "BPMN conversion failed" });
      }
    };
    
    convertXmlToSvg();

    // Cleanup function to destroy the viewer instance.
    return () => {
      bpmnViewer.destroy();
    };
  }, [props.args.xml]); // Dependency array ensures this runs when xml changes.

  return (
    <div 
      ref={containerRef} 
      style={{ height: 0, overflow: 'hidden' }}
    ></div>
  );
}

export default withStreamlitConnection(BPMN2Image);