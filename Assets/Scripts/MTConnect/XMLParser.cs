using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Xml;
using System;
using System.Xml.Linq;
using System.IO;
using UnityEngine.Networking;

namespace MyVC
{
    public class XMLParser : MonoBehaviour
    {
        public string ip;
        public int port;
        private XmlTextReader xmltxt;
        private string url;
        public float refreshInterval = 1f;

        private Dictionary<string, double> jointValues = new Dictionary<string, double>();
        void Start()
        {
            url = $"http://localhost:{port}/current";
            StartCoroutine(GetMTConnectData());
        }
        IEnumerator GetMTConnectData()
        {
            while (true)
            {
                float startTime = Time.time; // Coroutine ���� �ð� ���

                UnityWebRequest request = UnityWebRequest.Get(url);
                yield return request.SendWebRequest();

                // ���� Ȯ��
                if (request.result != UnityWebRequest.Result.Success)
                {
                    Debug.LogError("HTTP ��û ����: " + request.error);
                }
                else
                {
                    // XML ������ �޾�����, XmlTextReader ����
                    string xmlResponse = request.downloadHandler.text;
                    List<string> DeviceUUIDs = ReadDeviceIDs(xmlResponse);
                    foreach (string Device in DeviceUUIDs)
                    {
                        ReadJointValues(Device, xmlResponse);
                        RenderUtils.DeviceRendering(Device, jointValues);
                    }
                }

                float endTime = Time.time; // ��û �� �ð� ���
                float elapsedTime = endTime - startTime; // ���࿡ �ɸ� �ð� ���

                //Debug.Log($"Coroutine ���� �ð�: {elapsedTime}��");

                yield return new WaitForSeconds(refreshInterval);
            }
        }

        bool IsJoint(string name)
        {
            return name.EndsWith("j0") || name.EndsWith("j1") || name.EndsWith("j2") ||
                   name.EndsWith("j3") || name.EndsWith("j4") || name.EndsWith("j5");
        }
        List<string> ReadDeviceIDs(string xmlResponse)
        {
            StringReader stringReader = new StringReader(xmlResponse);
            xmltxt = new XmlTextReader(stringReader);
            xmltxt.WhitespaceHandling = WhitespaceHandling.None;

            List<string> deviceUUIDs = new List<string>();
            deviceUUIDs.Clear();

            while (xmltxt.Read())
            {
                if (xmltxt.NodeType == XmlNodeType.Element && xmltxt.Name == "DeviceStream" && xmltxt.GetAttribute("name").EndsWith("Adapter"))
                {
                    string uuid = xmltxt.GetAttribute("uuid");
                    if (!string.IsNullOrEmpty(uuid))
                    {
                        deviceUUIDs.Add(uuid);
                    }
                }
            }
            // XML ������ �ٽ� ó������ �ǵ��� (�ٽ� �б� ����)
            xmltxt.MoveToElement();
            return deviceUUIDs;
        }
        void ReadJointValues(string DeviceUUID, string xmlResponse)
        {
            StringReader stringReader = new StringReader(xmlResponse);
            xmltxt = new XmlTextReader(stringReader);
            xmltxt.WhitespaceHandling = WhitespaceHandling.None;

            jointValues.Clear();
            bool isTargetDevice = false;

            while (xmltxt.Read())
            {
                if (xmltxt.NodeType == XmlNodeType.Element)
                {
                    // DeviceStream �±׿��� UUID Ȯ��
                    if (xmltxt.Name == "DeviceStream")
                    {
                        string uuid = xmltxt.GetAttribute("uuid");
                        isTargetDevice = (uuid == DeviceUUID);
                    }
                    // �ش� UUID�� Joint ���� �б�
                    if (isTargetDevice && xmltxt.Name == "JointAngle")
                    {
                        string name = xmltxt.GetAttribute("name");

                        if (name != null && IsJoint(name))
                        {
                            xmltxt.Read();
                            if (xmltxt.NodeType == XmlNodeType.Text)
                            {
                                double value = Convert.ToDouble(xmltxt.Value);
                                jointValues[name] = value;
                            }
                        }
                    }
                }
            }
            // XML ������ �ٽ� ó������ �ǵ��� (���� �����ϵ���)
            xmltxt.MoveToElement();
        }
    }
}

