#!/usr/bin/env bash

set -e

# ==========================================
# TALON VISION - SIMULATION STARTER
# ==========================================

PROJECT_DIR="$HOME/TALON_VISION"
PX4_DIR="$HOME/PX4-Autopilot"

PIDS=()

# ------------------------------------------
# SISTEMI KAPATMA
# ------------------------------------------

cleanup() {
    echo ""
    echo "TALON_VISION kapatiliyor..."

    trap - EXIT INT TERM

    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    wait 2>/dev/null || true

    echo "Kapatma sinyalleri gonderildi."
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ------------------------------------------
# ROS 2 ORTAMI
# ------------------------------------------

source /opt/ros/lyrical/setup.bash

# VS Code Snap kaynakli grafik kutuphanesi
# cakismasini onlemek icin:

unset GTK_PATH
unset LD_PRELOAD
unset LD_AUDIT

echo ""
echo "========================================"
echo "         TALON VISION SYSTEM"
echo "========================================"
echo ""

# ------------------------------------------
# 1. PX4 + GAZEBO
# ------------------------------------------

echo "[1/5] PX4 ve Gazebo baslatiliyor..."

(
    cd "$PX4_DIR"
    PX4_GZ_WORLD=lawn make px4_sitl gz_advanced_plane
) &

PIDS+=($!)

# ------------------------------------------
# 2. GAZEBO SERVISINI BEKLE
# ------------------------------------------

echo "[2/5] Gazebo servisleri bekleniyor..."

READY=0

for i in {1..90}; do

    if gz service -l 2>/dev/null | grep -q '^/world/lawn/create$'; then
        READY=1
        break
    fi

    sleep 2
done

if [ "$READY" -ne 1 ]; then
    echo "HATA: Gazebo baslatilamadi."
    exit 1
fi

echo "Gazebo servisi hazir."


# ------------------------------------------
# 4. ROS 2 KAMERA KOPRUSU
# ------------------------------------------

echo "[4/5] ROS 2 kamera koprusu baslatiliyor..."

ros2 run ros_gz_bridge parameter_bridge \
    '/front_camera/image@sensor_msgs/msg/Image@gz.msgs.Image' &

PIDS+=($!)

# ------------------------------------------
# 5. HEDEF UCAK
# ------------------------------------------

echo "[5/5] Hedef ucak olusturuluyor..."

# Once varsa eski hedefi kaldir
gz service -s /world/lawn/remove \
    --reqtype gz.msgs.Entity \
    --reptype gz.msgs.Boolean \
    --timeout 5000 \
    --req 'name: "target_aircraft", type: MODEL' \
    >/dev/null 2>&1 || true

# Hedef ucagi olustur
gz service -s /world/lawn/create \
    --reqtype gz.msgs.EntityFactory \
    --reptype gz.msgs.Boolean \
    --timeout 10000 \
    --req "sdf_filename: \"$PX4_DIR/Tools/simulation/gz/models/rc_cessna/model.sdf\", name: \"target_aircraft\", pose: {position: {x: 5, y: 0, z: 1.5}}"

# Hedef ucagin hareketini baslat
echo "Hedef ucak hareket sistemi baslatiliyor..."

python3 "$PROJECT_DIR/simulation/target_aircraft.py" &

PIDS+=($!)

# ------------------------------------------
# 6. YOLO HEDEF TESPITI
# ------------------------------------------

echo "YOLO hedef tespiti baslatiliyor..."

sleep 3

cd "$PROJECT_DIR"

python3 vision/detector.py &

PIDS+=($!)

# ------------------------------------------
# SISTEM HAZIR
# ------------------------------------------

echo ""
echo "========================================"
echo "      TALON VISION BASLATILDI"
echo "========================================"
echo ""
echo "PX4                 : AKTIF"
echo "Gazebo              : BASLATILDI"
echo "ROS 2 Kamera        : BASLATILDI"
echo "Target Aircraft     : BASLATILDI"
echo "YOLO                : BASLATILDI"
echo ""
echo "Sistemi kapatmak icin CTRL+C"
echo ""

wait