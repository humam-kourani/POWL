import BPMN2Image from './components/BPMN2Image.tsx'; // Make sure the component name matches
import React from 'react';
import ReactDOM from 'react-dom/client';

// A sample BPMN diagram string to use for testing
const sampleBpmnXml = `
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Process Started"/>
    <bpmn:task id="Task_1" name="Do Something"/>
    <bpmn:endEvent id="EndEvent_1" name="Process Ended"/>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1"><dc:Bounds x="173" y="102" width="36" height="36"/><bpmndi:BPMNLabel><dc:Bounds x="155" y="145" width="73" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1un6b3p_di" bpmnElement="Task_1"><dc:Bounds x="270" y="80" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Event_020j81l_di" bpmnElement="EndEvent_1"><dc:Bounds x="432" y="102" width="36" height="36"/><bpmndi:BPMNLabel><dc:Bounds x="414" y="145" width="72" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_0n95k2i_di" bpmnElement="Flow_1"><di:waypoint x="209" y="120"/><di:waypoint x="270" y="120"/></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1u8h9xl_di" bpmnElement="Flow_2"><di:waypoint x="370" y="120"/><di:waypoint x="432" y="120"/></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
`;

// This part simulates Streamlit's "args" by passing the xml as a prop
const args = { xml: sampleBpmnXml };

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <BPMN2Image args={args} />
  </React.StrictMode>
);