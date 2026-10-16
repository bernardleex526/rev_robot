#include "m20_slam_navigation/common/params.hpp"
#include "m20_slam_navigation/control/local_controller_node.hpp"
#include "m20_slam_navigation/planning/hybrid_astar.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <vector>

using m20::Scalar;
using Vec3 = Eigen::Matrix<Scalar, 3, 1>;

namespace {

Scalar distToPolyline(const Vec3& p, const std::vector<Vec3>& path) {
  Scalar best = std::numeric_limits<Scalar>::max();
  for (size_t i = 1; i < path.size(); ++i) {
    const Eigen::Matrix<Scalar, 2, 1> a = path[i - 1].head<2>();
    const Eigen::Matrix<Scalar, 2, 1> b = path[i].head<2>();
    const Eigen::Matrix<Scalar, 2, 1> q = p.head<2>();
    const Eigen::Matrix<Scalar, 2, 1> ab = b - a;
    const Scalar len2 = ab.squaredNorm();
    const Scalar t = len2 > 0 ? std::clamp((q - a).dot(ab) / len2, Scalar(0), Scalar(1)) : 0;
    best = std::min(best, (a + t * ab - q).norm());
  }
  return best;
}

struct Scenario {
  const char* name;
  Vec3 start;
  Vec3 goal;
  bool wall;
  int mode;  // 0=auto, 1=force line, 2=force DWA
};

}  // namespace

int main(int argc, char** argv) {
  const int only = argc > 1 ? std::atoi(argv[1]) : -1;
  const bool dump = argc > 2;
  constexpr int W = 200, H = 200;
  constexpr Scalar RES = 0.05, ORIGIN = -5.0, DT = 0.02;

  const Scenario scenarios[] = {
      {"straight_6m", Vec3(-3.0, 0.0, 0.0), Vec3(3.0, 0.0, 0.0), false, 1},
      {"diagonal_free", Vec3(-3.5, -3.5, 0.785398), Vec3(3.0, 2.5, 0.785398), false, 1},
      {"detour_wall", Vec3(-3.5, 0.0, 0.0), Vec3(3.5, 0.0, 0.0), true, 0},
  };

  std::setvbuf(stdout, nullptr, _IOLBF, 0);
  int failures = 0;
  for (int si = 0; si < 3; ++si) {
    if (only >= 0 && si != only) continue;
    const auto& sc = scenarios[si];
    std::printf("[%s] planning...\n", sc.name);
    std::vector<uint8_t> costmap(W * H, 0);
    if (sc.wall) {
      for (int y = 0; y < H; ++y) {
        const Scalar wy = ORIGIN + (y + 0.5) * RES;
        if (wy < -1.5) continue;
        for (int x = 0; x < W; ++x) {
          const Scalar wx = ORIGIN + (x + 0.5) * RES;
          if (std::abs(wx) < 0.2) costmap[y * W + x] = 254;
        }
      }
    }

    m20::GlobalPlannerParams gp;
    gp.time_limit_sec = 2.0;
    gp.astar_time = 2.0;
    gp.max_expansions = 400000;
    m20::TerrainParams terrain;
    m20::planning::HybridAStar planner(gp, terrain);
    const auto path = planner.plan(costmap, W, H, RES, ORIGIN, ORIGIN, sc.start, sc.goal);
    if (path.empty()) {
      std::printf("%-14s PLAN_FAILED\n", sc.name);
      ++failures;
      continue;
    }
    std::printf("[%s] planned %zu pts\n", sc.name, path.size());
    if (dump)
      for (const auto& p : path) std::printf("    path %.3f %.3f %.3f\n", p.x(), p.y(), p.z());
    Scalar plan_len = 0;
    for (size_t i = 1; i < path.size(); ++i) plan_len += (path[i] - path[i - 1]).head<2>().norm();

    m20::LocalControllerParams lp;
    lp.direct_line_mode = true;
    lp.num_vx_samples = 11;
    lp.num_vy_samples = 5;
    lp.num_omega_samples = 11;
    lp.weight_smoothness = 0.0;
    lp.velocity_accel_threshold = 3.0;
    m20::control::LocalControllerNode ctrl(lp);
    ctrl.setPlannerMode(sc.mode);
    Vec3 pose = sc.start;
    m20::control::VelocityCommand vel{};
    Scalar max_dev = 0, max_transit_dev = 0, sum_dev = 0, t = 0;
    int n = 0;
    bool collided = false;
    const Scalar t_max = 60.0;
    const Scalar arrive = lp.stop_distance + 0.05;
    int still = 0;
    const int ctrl_div = static_cast<int>(std::round(0.1 / DT));  // 10 Hz control loop
    while (t < t_max && still < 50) {
      if (n % ctrl_div == 0) {
        vel = ctrl.step(pose, vel, path, costmap, W, H, RES, ORIGIN, ORIGIN);
      }
      const Scalar c = std::cos(pose.z()), s = std::sin(pose.z());
      pose.x() += (c * vel.vx - s * vel.vy) * DT;
      pose.y() += (s * vel.vx + c * vel.vy) * DT;
      pose.z() += vel.omega * DT;
      const int cx = static_cast<int>((pose.x() - ORIGIN) / RES);
      const int cy = static_cast<int>((pose.y() - ORIGIN) / RES);
      if (cx >= 0 && cy >= 0 && cx < W && cy < H && costmap[cy * W + cx] >= 254) collided = true;
      const Scalar cur_goal_dist = (pose - sc.goal).head<2>().norm();
      const Scalar d = distToPolyline(pose, path);
      if (cur_goal_dist > arrive) {
        max_transit_dev = std::max(max_transit_dev, d);
      }
      max_dev = std::max(max_dev, d);
      sum_dev += d;
      ++n;
      t += DT;
      if (std::abs(vel.vx) + std::abs(vel.vy) + std::abs(vel.omega) < 1e-6) ++still; else still = 0;
      if (n % (dump ? 25 : 250) == 0)
        std::printf("  t=%.1f pose=(%.2f,%.2f,%.2f) v=(%.2f,%.2f,%.2f) dev=%.3f mode=%d\n", t, pose.x(), pose.y(),
                    pose.z(), vel.vx, vel.vy, vel.omega, d, ctrl.getMode() == m20::control::LocalControllerNode::Mode::LINE);
    }
    const Scalar goal_err = (pose - sc.goal).head<2>().norm();
    const Scalar dev_mean = n ? sum_dev / n : 0.0;
    const bool ok = goal_err <= arrive && !collided && (sc.wall ? (dev_mean < 0.3) : (max_transit_dev < 0.3));
    if (!ok) ++failures;
    std::printf("%-14s plan_pts=%3zu plan_len=%.2fm  t=%.1fs  goal_err=%.3fm  dev_mean=%.3fm dev_transit=%.3fm dev_max=%.3fm collided=%d  %s\n",
                sc.name, path.size(), plan_len, t, goal_err, dev_mean, max_transit_dev, max_dev,
                collided ? 1 : 0, ok ? "PASS" : "FAIL");
  }
  std::printf("%s\n", failures ? "SOME FAILED" : "ALL PASS");
  return failures ? 1 : 0;
}
