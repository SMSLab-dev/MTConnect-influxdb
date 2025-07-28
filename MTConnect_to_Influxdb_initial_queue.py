import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# DSR 초기값 받아오기 위한 라이브러리 임포트
import rospy
from std_msgs.msg import Float64MultiArray
import std_msgs
from std_msgs.msg import String

sys.dont_write_bytecode = True
sys.path.append(os.path.abspath((os.path.join(os.path.dirname(__file__),"/home/sms/catkin_ws/src/doosan-robot/common/imp"))))

from DSR_ROBOT import *

# InfluxDB 설정
INFLUXDB_URL = "http://localhost:8086/write?db=robot"
INFLUXDB_TOKEN = "your_token"

# MTConnect Agent 설정
MTCONNECT_URL = "http://localhost:5001/current"

headers = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 저장할 데이터 리스트 (robot_mode_id 제외)
VALID_DATA_ITEMS = [
    "A0912_j0", "A0912_j1", "A0912_j2", "A0912_j3", "A0912_j4", "A0912_j5",
    "A0912_X", "A0912_Y", "A0912_Z",
    "A0912_Rx", "A0912_Ry", "A0912_Rz",
    "A0912_solutionspace", "A0912_mode_id"
    "M1013_j0", "M1013_j1", "M1013_j2", "M1013_j3", "M1013_j4", "M1013_j5",
    "M1013_X", "M1013_Y", "M1013_Z",
    "M1013_Rx", "M1013_Ry", "M1013_Rz",
    "M1013_solutionspace", "M1013_mode_id",
    "Switch"
]

def get_mtconnect_data():
    """MTConnect Agent에서 데이터 가져오기"""
    response = requests.get(MTCONNECT_URL)
    
    if response.status_code == 200:
        return response.text # XML 데이터 반환
    else:
        print(f"❌ MTConnect 데이터 수신 실패: {response.status_code}")
        return None

def parse_mtconnect_data(xml_data):
    """MTConnect XML 데이터를 파싱하여 InfluxDB용 데이터 포맷으로 변환"""
    root = ET.fromstring(xml_data)
    ns = {'mt': 'urn:mtconnect.org:MTConnectStreams:2.3'}
    data_list = []

    for device in root.findall(".//mt:DeviceStream", ns):
        uuid = device.get("uuid", "UNKNOWN")
        device_name = device.get("name")
        # print(device_name)

        for component in device.findall(".//mt:ComponentStream", ns):
            for event in component.findall(".//mt:Events/*", ns):
                data_id = event.get("dataItemId")
                if data_id not in VALID_DATA_ITEMS:
                    continue

                value = event.text
                if value == "UNAVAILABLE":
                    continue

                timestamp_str = event.get("timestamp")
                try:
                    # 마이크로초(µs)에서 나노초(ns)로 변환
                    timestamp = int(datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1e9)
                except ValueError:
                    print(f"⛔ Timestamp format error: {timestamp_str}")
                    continue

                if data_id == "solutionspace":
                    value = f"{int(float(value))}i" # 정수 값에 `i` 추가
                else:
                    value = float(value) # 부동소수점 값 변환

                line_protocol = f"mtconnect,uuid={uuid},device={device_name} {data_id}={value} {timestamp}"
                data_list.append(line_protocol)

            for sample in component.findall(".//mt:Samples/*", ns):
                data_id = sample.get("dataItemId")
                if data_id not in VALID_DATA_ITEMS:
                    continue

                value = sample.text
                if value == "UNAVAILABLE":
                    continue

                timestamp_str = sample.get("timestamp")
                try:
                    # 마이크로초(µs)에서 나노초(ns)로 변환
                    timestamp = int(datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1e9)
                    print(timestamp_str)
                except ValueError:
                    print(f"⛔ Timestamp format error: {timestamp_str}")
                    continue

                if data_id == "solutionspace":
                    value = f"{int(float(value))}i"
                else:
                    value = float(value)

                line_protocol = f"mtconnect,uuid={uuid},device={device_name} {data_id}={value} {timestamp}"
                data_list.append(line_protocol)
                print(line_protocol)

    return data_list

def write_to_influxdb(data_list):
    """InfluxDB에 모든 데이터 저장"""
    if not data_list:
        return

    data = "\n".join(data_list)
    response = requests.post(INFLUXDB_URL, headers=headers, data=data)

    if response.status_code == 204:
        print(f"✅ InfluxDB에 데이터 저장 완료: {len(data_list)}개 데이터")
    else:
        print("Recorded")
        # print(f"❌ InfluxDB 저장 실패: {response.status_code} {response.text}")

def get_initial_robot_data(timestamp):
    from dsr_msgs.srv import GetCurrentPosj, GetCurrentPosx, GetCurrentTcp, GetCurrentSolutionSpace, GetRobotMode

    def call_service(ns, service, srv_type):
        full = f"/dsr01{ns.lower()}/{service}"
        rospy.wait_for_service(full)
        try:
            client = rospy.ServiceProxy(full, srv_type)
            return client()
        except rospy.ServiceException as e:
            rospy.logerr(f"{full} failed: {e}")
            return None

    data_list = []

    # for ns in ["a0912", "m1013"]:
    for ns in ["a0912"]:
        prefix = ns.upper()
        posj = call_service(ns, "aux_control/get_current_posj", GetCurrentPosj)
        posx = call_service(ns, "aux_control/get_current_posx", GetCurrentPosx)
        sol = call_service(ns, "aux_control/get_current_solution_space", GetCurrentSolutionSpace)
        mode = call_service(ns, "system/get_robot_mode", GetRobotMode)

        if posj:
            fields = ",".join([f"{prefix}_j{i}={posj.pos[i]:.2f}" for i in range(6)])
            data_list.append(f"mtconnect,uuid={prefix},device={prefix} {fields} {timestamp}")
        if posx:
            p = posx.task_pos_info[0].data
            fields = ",".join([
                f"{prefix}_X={p[0]:.2f}", f"{prefix}_Y={p[1]:.2f}", f"{prefix}_Z={p[2]:.2f}",
                f"{prefix}_Rx={p[3]:.2f}", f"{prefix}_Ry={p[4]:.2f}", f"{prefix}_Rz={p[5]:.2f}"
            ])
            data_list.append(f"mtconnect,uuid={prefix},device={prefix} {fields} {timestamp}")
        if sol:
            data_list.append(f"mtconnect,uuid={prefix},device={prefix} {prefix}_solutionspace={int(sol.sol_space)}i {timestamp}")
        if mode:
            data_list.append(f"mtconnect,uuid={prefix},device={prefix} {prefix}_mode_id={int(mode.robot_mode)}i {timestamp}")

    return data_list

def write_initial_to_influxdb(timestamp):
    rospy.init_node("initial_influxdb_writer", anonymous=True)
    data = get_initial_robot_data(timestamp)
    if data:
        write_to_influxdb(data)
        print("✅ 초기값 InfluxDB에 저장 완료")


if __name__ == '__main__':
    common_timestamp = int(time.time() * 1e9)

    write_initial_to_influxdb(common_timestamp)

    while True:
        xml_data = get_mtconnect_data()
        if xml_data:
            data_list = parse_mtconnect_data(xml_data)
            write_to_influxdb(data_list)

