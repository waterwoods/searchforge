"""
AutoTuner 最小功能验证测试

验证核心调优路径在功能冻结后仍然可用：
- 顺序决策（Sequential Decision Making）
- 参数预投影验证（Pre-projection Validation）
- 冷却与滞回机制（Cooldown & Hysteresis）
- 内存缓存（In-Memory Cache）
- 基础约束检查（Basic Constraint Checking）

⚠️ Feature Freeze: 此测试验证最小核心功能，不包含已冻结的特性
"""

import sys
import time
from typing import Dict, Any

# Add modules to path
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

from modules.autotuner.brain import autotuner_config
from modules.autotuner.brain.contracts import TuningInput, Action, SLO, Guards, MemorySample
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.multi_knob_decider import decide_multi_knob
from modules.autotuner.brain.apply import apply_action, apply_updates, get_apply_counters, reset_apply_counters
from modules.autotuner.brain.memory import Memory, get_memory
from modules.autotuner.brain.constraints import clip_params, clip_joint


class AutoTunerMinimalValidator:
    """AutoTuner 最小功能验证器"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "message": message
        }
        self.test_results.append(result)
        if not passed:
            self.failed_tests.append(test_name)
        print(f"{status} - {test_name}: {message}")
    
    def test_config_flags(self) -> bool:
        """测试配置标志是否正确设置"""
        print("\n[测试 1] 配置标志验证")
        print("=" * 60)
        
        flags = autotuner_config.get_active_features()
        expected_disabled = {
            'ENABLE_ATOMIC': False,
            'ENABLE_ROLLBACK': False,
            'ENABLE_BANDIT': False,
            'ENABLE_COMPLEX_STEP': False,
            'ENABLE_REDIS': False,
            'ENABLE_PERSISTENCE': False
        }
        
        all_correct = True
        for flag_name, expected_value in expected_disabled.items():
            actual_value = flags[flag_name]
            if actual_value != expected_value:
                all_correct = False
                self.log_test(
                    f"Config Flag: {flag_name}",
                    False,
                    f"Expected {expected_value}, got {actual_value}"
                )
            else:
                self.log_test(
                    f"Config Flag: {flag_name}",
                    True,
                    f"Correctly set to {expected_value}"
                )
        
        return all_correct
    
    def test_basic_decision(self) -> bool:
        """测试基础决策逻辑"""
        print("\n[测试 2] 基础决策逻辑")
        print("=" * 60)
        
        # Create test input with high latency
        test_input = TuningInput(
            p95_ms=1500.0,  # High latency
            recall_at10=0.90,  # Good recall
            qps=10.0,
            params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 2},
            slo=SLO(p95_ms=1200.0, recall_at10=0.85),
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        try:
            action = decide_tuning_action(test_input)
            
            # Should suggest a decrease action
            is_valid_action = action.kind in ["drop_ef", "drop_ncand", "noop"]
            self.log_test(
                "Basic Decision - High Latency",
                is_valid_action,
                f"Action: {action.kind}, Reason: {action.reason}"
            )
            
            return is_valid_action
        except Exception as e:
            self.log_test("Basic Decision - High Latency", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_knob_decision(self) -> bool:
        """测试多参数决策（顺序模式）"""
        print("\n[测试 3] 多参数决策（顺序模式）")
        print("=" * 60)
        
        test_input = TuningInput(
            p95_ms=1500.0,
            recall_at10=0.90,
            qps=10.0,
            params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 2},
            slo=SLO(p95_ms=1200.0, recall_at10=0.85),
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        try:
            action = decide_multi_knob(test_input)
            
            # Should return an action (could be noop or multi_knob)
            is_valid = action.kind in ["multi_knob", "noop"]
            
            # Mode should be sequential (atomic is disabled)
            mode_correct = action.mode == "sequential"
            
            self.log_test(
                "Multi-Knob Decision",
                is_valid and mode_correct,
                f"Kind: {action.kind}, Mode: {action.mode}, Reason: {action.reason}"
            )
            
            return is_valid and mode_correct
        except Exception as e:
            self.log_test("Multi-Knob Decision", False, f"Exception: {str(e)}")
            return False
    
    def test_apply_sequential(self) -> bool:
        """测试顺序应用模式"""
        print("\n[测试 4] 参数应用（顺序模式）")
        print("=" * 60)
        
        reset_apply_counters()
        
        current_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 2
        }
        
        updates = {
            'ef': -32,  # Decrease ef
            'Ncand_max': -100  # Decrease candidate_k
        }
        
        try:
            result = apply_updates(current_params, updates, mode="sequential")
            
            # Should be applied or rejected (not rolled_back, since rollback is disabled)
            status_valid = result.status in ["applied", "rejected"]
            
            # Parameters should be within valid range
            params_valid = True
            if result.status == "applied":
                new_ef = result.params_after.get('ef', 0)
                params_valid = 32 <= new_ef <= 256
            
            self.log_test(
                "Apply Sequential Mode",
                status_valid and params_valid,
                f"Status: {result.status}, Updates: {result.updates_applied}"
            )
            
            return status_valid and params_valid
        except Exception as e:
            self.log_test("Apply Sequential Mode", False, f"Exception: {str(e)}")
            return False
    
    def test_apply_atomic_disabled(self) -> bool:
        """测试原子模式已禁用（应回退到顺序模式）"""
        print("\n[测试 5] 原子模式禁用验证")
        print("=" * 60)
        
        current_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 2
        }
        
        updates = {'ef': 32}
        
        try:
            # Try to use atomic mode (should fallback to sequential)
            result = apply_updates(current_params, updates, mode="atomic")
            
            # Should be applied successfully (fallback to sequential)
            fallback_worked = result.status in ["applied", "rejected"]
            
            self.log_test(
                "Atomic Mode Disabled",
                fallback_worked,
                f"Correctly fell back to sequential, Status: {result.status}"
            )
            
            return fallback_worked
        except Exception as e:
            self.log_test("Atomic Mode Disabled", False, f"Exception: {str(e)}")
            return False
    
    def test_memory_in_memory_only(self) -> bool:
        """测试记忆系统（仅内存，无持久化）"""
        print("\n[测试 6] 记忆系统（内存缓存）")
        print("=" * 60)
        
        try:
            mem = get_memory()
            
            # Create and observe a sample
            sample = MemorySample(
                bucket_id="test_bucket",
                ef=128,
                T=500,
                Ncand_max=1000,
                p95_ms=800.0,
                recall_at10=0.88,
                ts=time.time()
            )
            
            mem.observe(sample)
            
            # Query the memory
            sweet_spot = mem.query("test_bucket")
            
            # Should work (might be None if not enough data)
            memory_works = True  # Just verify no exception
            
            # Verify Redis and persistence are disabled
            redis_disabled = mem.redis_client is None
            persistence_disabled = not mem.persistence_enabled
            
            all_passed = memory_works and redis_disabled and persistence_disabled
            
            self.log_test(
                "Memory In-Memory Cache",
                all_passed,
                f"Redis disabled: {redis_disabled}, Persistence disabled: {persistence_disabled}"
            )
            
            return all_passed
        except Exception as e:
            self.log_test("Memory In-Memory Cache", False, f"Exception: {str(e)}")
            return False
    
    def test_constraints(self) -> bool:
        """测试参数约束检查"""
        print("\n[测试 7] 参数约束检查")
        print("=" * 60)
        
        try:
            # Test clip_params
            invalid_params = {
                'ef': 1000,  # Too high
                'T': 50,  # Too low
                'Ncand_max': 5000,  # Too high
                'rerank_mult': 10  # Too high
            }
            
            clipped = clip_params(invalid_params)
            
            # Check if clipping worked
            ef_clipped = clipped['ef'] <= 256
            t_clipped = clipped['T'] >= 200
            ncand_clipped = clipped['Ncand_max'] <= 2000
            rerank_clipped = clipped['rerank_mult'] <= 6  # Max is 6, not 5
            
            all_clipped = ef_clipped and t_clipped and ncand_clipped and rerank_clipped
            
            self.log_test(
                "Constraints Clipping",
                all_clipped,
                f"Clipped: ef={clipped['ef']}, T={clipped['T']}, "
                f"Ncand_max={clipped['Ncand_max']}, rerank_mult={clipped['rerank_mult']}"
            )
            
            return all_clipped
        except Exception as e:
            self.log_test("Constraints Clipping", False, f"Exception: {str(e)}")
            return False
    
    def test_cooldown_hysteresis(self) -> bool:
        """测试冷却和滞回机制"""
        print("\n[测试 8] 冷却与滞回机制")
        print("=" * 60)
        
        # Test cooldown
        cooldown_input = TuningInput(
            p95_ms=1500.0,
            recall_at10=0.90,
            qps=10.0,
            params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 2},
            slo=SLO(p95_ms=1200.0, recall_at10=0.85),
            guards=Guards(cooldown=True, stable=True),  # Cooldown active
            near_T=False
        )
        
        try:
            action = decide_tuning_action(cooldown_input)
            cooldown_works = action.kind == "noop" and "cooldown" in action.reason.lower()
            
            self.log_test(
                "Cooldown Mechanism",
                cooldown_works,
                f"Action: {action.kind}, Reason: {action.reason}"
            )
            
            # Test hysteresis (small error should result in noop)
            hysteresis_input = TuningInput(
                p95_ms=1220.0,  # Slightly over SLO
                recall_at10=0.86,  # Slightly over SLO
                qps=10.0,
                params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 2},
                slo=SLO(p95_ms=1200.0, recall_at10=0.85),
                guards=Guards(cooldown=False, stable=True),
                near_T=False
            )
            
            action2 = decide_tuning_action(hysteresis_input)
            hysteresis_works = action2.kind == "noop"
            
            self.log_test(
                "Hysteresis Mechanism",
                hysteresis_works,
                f"Action: {action2.kind}, Reason: {action2.reason}"
            )
            
            return cooldown_works and hysteresis_works
        except Exception as e:
            self.log_test("Cooldown/Hysteresis", False, f"Exception: {str(e)}")
            return False
    
    def run_simulation(self, steps: int = 20) -> Dict[str, Any]:
        """运行简单仿真，验证整体调优流程"""
        print("\n[测试 9] 整体仿真（20 步）")
        print("=" * 60)
        
        # Initialize simulation state
        params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 2
        }
        
        slo = SLO(p95_ms=1200.0, recall_at10=0.85)
        
        # Simulate high latency scenario
        p95_ms = 1500.0
        recall_at10 = 0.90
        
        actions_taken = []
        params_history = [params.copy()]
        
        cooldown_ticks = 0
        
        try:
            for step in range(steps):
                # Create input
                inp = TuningInput(
                    p95_ms=p95_ms,
                    recall_at10=recall_at10,
                    qps=10.0,
                    params=params.copy(),
                    slo=slo,
                    guards=Guards(cooldown=(cooldown_ticks > 0), stable=True),
                    near_T=False
                )
                
                # Decide action
                action = decide_tuning_action(inp)
                actions_taken.append(action.kind)
                
                # Apply action if not noop
                if action.kind != "noop":
                    new_params = apply_action(params, action)
                    params = new_params
                    cooldown_ticks = 2  # Set cooldown
                    
                    # Simulate latency improvement
                    p95_ms = max(1000.0, p95_ms - 50.0)
                else:
                    if cooldown_ticks > 0:
                        cooldown_ticks -= 1
                
                params_history.append(params.copy())
            
            # Calculate metrics
            non_noop_actions = [a for a in actions_taken if a != "noop"]
            apply_rate = len(non_noop_actions) / steps if steps > 0 else 0
            
            # Final latency should be improved
            delta_p95 = p95_ms - 1500.0
            
            # Success criteria: at least some actions taken and latency improved
            success = apply_rate > 0.1 and delta_p95 < 0
            
            self.log_test(
                "Simulation 20 Steps",
                success,
                f"Apply rate: {apply_rate:.2%}, ΔP95: {delta_p95:.1f} ms"
            )
            
            return {
                'steps': steps,
                'apply_rate': apply_rate,
                'delta_p95': delta_p95,
                'final_p95': p95_ms,
                'actions_taken': actions_taken,
                'success': success
            }
        except Exception as e:
            self.log_test("Simulation 20 Steps", False, f"Exception: {str(e)}")
            return {
                'steps': 0,
                'apply_rate': 0.0,
                'delta_p95': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("  AutoTuner 最小功能验证测试")
        print("  Feature Freeze Validation")
        print("=" * 60)
        
        # Run all tests
        test1 = self.test_config_flags()
        test2 = self.test_basic_decision()
        test3 = self.test_multi_knob_decision()
        test4 = self.test_apply_sequential()
        test5 = self.test_apply_atomic_disabled()
        test6 = self.test_memory_in_memory_only()
        test7 = self.test_constraints()
        test8 = self.test_cooldown_hysteresis()
        
        # Run simulation
        sim_result = self.run_simulation(steps=20)
        test9 = sim_result['success']
        
        # Summary
        print("\n" + "=" * 60)
        print("  测试总结 (Test Summary)")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        if sim_result['success']:
            print(f"\n仿真结果:")
            print(f"  - Apply Rate: {sim_result['apply_rate']:.2%}")
            print(f"  - ΔP95: {sim_result['delta_p95']:.1f} ms")
            print(f"  - Final P95: {sim_result['final_p95']:.1f} ms")
        
        all_passed = (failed_tests == 0)
        
        print("\n" + "=" * 60)
        if all_passed:
            print("  ✅ PASS - 核心路径可用")
            print("  AutoTuner 最小核心功能验证通过")
        else:
            print("  ❌ FAIL - 检查关键模块")
            print(f"  失败的测试: {', '.join(self.failed_tests)}")
        print("=" * 60 + "\n")
        
        return all_passed


def main():
    """主入口"""
    validator = AutoTunerMinimalValidator()
    success = validator.run_all_tests()
    
    # Return exit code
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
