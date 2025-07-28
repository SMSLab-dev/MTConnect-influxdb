using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace MyVC
{
    public static class RenderUtils
    {
        public static void DeviceRendering(string Device, Dictionary<string, double> jointValues)
        {
            GameObject Robot = GameObject.Find(Device);

            if (Robot == null)
            {
                Debug.LogError($"Device with name '{Device}' not found in the scene.");
            }

            ArticulationBody[] foundLinks = Robot.GetComponentsInChildren<ArticulationBody>();

            // 3. "link1" ~ "link6" �̸��� ���� ������Ʈ�� ���͸� �� ����
            ArticulationBody[] links = foundLinks
                .Where(link => link.gameObject.name.StartsWith("link"))
                .OrderBy(link => int.Parse(link.gameObject.name.Substring(4)))  // "linkX"���� ���� �κи� �����Ͽ� ����
                .ToArray();

            RBRendering(links, jointValues);
        }
        public static void RBRendering(ArticulationBody[] links, Dictionary<string, double> jointValues)
        {
            ArticulationBody link0 = links[0];
            ArticulationBody link1 = links[1];
            ArticulationBody link2 = links[2];
            ArticulationBody link3 = links[3];
            ArticulationBody link4 = links[4];
            ArticulationBody link5 = links[5];

            ArticulationReducedSpace joint0 = new ArticulationReducedSpace((float)jointValues["A0912_j0"]*3.141592f/180f);
            ArticulationReducedSpace joint1 = new ArticulationReducedSpace((float)jointValues["A0912_j1"]*3.141592f/180f);
            ArticulationReducedSpace joint2 = new ArticulationReducedSpace((float)jointValues["A0912_j2"]*3.141592f/180f);
            ArticulationReducedSpace joint3 = new ArticulationReducedSpace((float)jointValues["A0912_j3"]*3.141592f/180f);
            ArticulationReducedSpace joint4 = new ArticulationReducedSpace((float)jointValues["A0912_j4"]*3.141592f/180f);
            ArticulationReducedSpace joint5 = new ArticulationReducedSpace((float)jointValues["A0912_j5"]*3.141592f/180f);

            link0.jointPosition = joint0;
            link1.jointPosition = joint1;
            link2.jointPosition = joint2;
            link3.jointPosition = joint3;
            link4.jointPosition = joint4;
            link5.jointPosition = joint5;
        }
    }
}
