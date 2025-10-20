import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp


class MonteCarloSimulator:
    """Advanced Monte Carlo simulation engine for Bihar election forecasting"""
    
    def __init__(self, model: Any, features_df: pd.DataFrame):
        self.model = model
        self.features_df = features_df.copy()
        self.n_constituencies = len(features_df)
        self.n_sims = Config.N_MONTE_CARLO_SIMS
        
        # Prepare base probabilities
        self._prepare_base_probabilities()
        
        print(f"✅ Monte Carlo simulator initialized for {self.n_constituencies} constituencies")
    
    def _prepare_base_probabilities(self):
        """Prepare base win probabilities for each constituency"""
        # Use existing probabilities or generate from model
        if 'final_nda_prob' in self.features_df.columns:
            self.base_probs = self.features_df['final_nda_prob'].values
        elif 'nda_win_prob' in self.features_df.columns:
            self.base_probs = self.features_df['nda_win_prob'].values
        else:
            # Generate probabilities from model if available
            if self.model is not None:
                try:
                    from src.modeling.model_updater import ModelUpdater
                    updater = ModelUpdater()
                    updater.model = self.model
                    predictions_df = updater.predict_constituencies(self.features_df)
                    self.base_probs = predictions_df['nda_win_probability'].values
                except Exception as e:
                    print(f"Warning: Could not generate model predictions: {e}")
                    # Fallback to poll-based probabilities
                    self.base_probs = 1 / (1 + np.exp(-self.features_df['poll_lead_nda'].values / 5))
            else:
                # Fallback to poll-based probabilities
                self.base_probs = 1 / (1 + np.exp(-self.features_df['poll_lead_nda'].values / 5))
        
        # Ensure probabilities are in valid range
        self.base_probs = np.clip(self.base_probs, 0.01, 0.99)
        
        print(f"   Base probabilities: NDA {(self.base_probs > 0.5).sum()}/{len(self.base_probs)} seats")
    
    def run_simulations(self, n_sims: int = None, uncertainty_factor: float = 1.0, 
                       correlation_factor: float = 0.3, parallel: bool = True) -> Dict:
        """Run Monte Carlo simulations with advanced uncertainty modeling"""
        if n_sims is None:
            n_sims = self.n_sims
        
        print(f"🔄 Running {n_sims:,} Monte Carlo simulations...")
        print(f"   Uncertainty factor: {uncertainty_factor:.2f}")
        print(f"   Correlation factor: {correlation_factor:.2f}")
        
        if parallel and n_sims >= 1000:
            results = self._run_parallel_simulations(n_sims, uncertainty_factor, correlation_factor)
        else:
            results = self._run_sequential_simulations(n_sims, uncertainty_factor, correlation_factor)
        
        # Calculate comprehensive statistics
        simulation_stats = self._calculate_simulation_statistics(results)
        
        print(f"✅ Simulations complete: {simulation_stats['mean_nda_seats']:.1f} ± {simulation_stats['std_nda_seats']:.1f} NDA seats")
        
        return {
            'simulation_results': results,
            'statistics': simulation_stats,
            'metadata': {
                'n_simulations': n_sims,
                'n_constituencies': self.n_constituencies,
                'uncertainty_factor': uncertainty_factor,
                'correlation_factor': correlation_factor,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _run_parallel_simulations(self, n_sims: int, uncertainty_factor: float, 
                                 correlation_factor: float) -> Dict:
        """Run simulations in parallel for better performance"""
        n_cores = min(mp.cpu_count(), 8)  # Limit to 8 cores
        sims_per_core = n_sims // n_cores
        
        print(f"   Running on {n_cores} cores ({sims_per_core:,} sims per core)")
        
        # Prepare arguments for parallel execution
        args_list = []
        for i in range(n_cores):
            start_sim = i * sims_per_core
            end_sim = (i + 1) * sims_per_core if i < n_cores - 1 else n_sims
            n_core_sims = end_sim - start_sim
            
            args_list.append((
                n_core_sims, 
                self.base_probs, 
                self.features_df, 
                uncertainty_factor, 
                correlation_factor,
                i  # seed offset
            ))
        
        # Run parallel simulations
        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            core_results = list(executor.map(self._simulate_batch, args_list))
        
        # Combine results
        all_nda_seats = []
        all_constituency_wins = []
        
        for core_result in core_results:
            all_nda_seats.extend(core_result['nda_seats'])
            all_constituency_wins.extend(core_result['constituency_wins'])
        
        return {
            'nda_seats': np.array(all_nda_seats),
            'constituency_wins': np.array(all_constituency_wins)
        }
    
    def _run_sequential_simulations(self, n_sims: int, uncertainty_factor: float, 
                                   correlation_factor: float) -> Dict:
        """Run simulations sequentially"""
        return self._simulate_batch((n_sims, self.base_probs, self.features_df, 
                                   uncertainty_factor, correlation_factor, 0))
    
    @staticmethod
    def _simulate_batch(args: Tuple) -> Dict:
        """Simulate a batch of elections (static method for multiprocessing)"""
        n_sims, base_probs, features_df, uncertainty_factor, correlation_factor, seed_offset = args
        
        # Set random seed for reproducibility
        np.random.seed(42 + seed_offset)
        
        n_constituencies = len(base_probs)
        nda_seats = []
        constituency_wins = []
        
        # Get uncertainty measures
        volatility = features_df.get('poll_volatility', pd.Series([2.5] * n_constituencies)).values
        uncertainty = features_df.get('poll_uncertainty', pd.Series([5.0] * n_constituencies)).values
        
        # Regional correlation matrix (simplified)
        regions = features_df['region'].values if 'region' in features_df.columns else ['Unknown'] * n_constituencies
        unique_regions = list(set(regions))
        region_indices = {region: i for i, region in enumerate(unique_regions)}
        
        for sim in range(n_sims):
            # Generate correlated random shocks
            regional_shocks = np.random.normal(0, 0.02, len(unique_regions))  # 2% regional shock
            national_shock = np.random.normal(0, 0.01)  # 1% national shock
            
            # Apply shocks to each constituency
            sim_probs = base_probs.copy()
            
            for i, region in enumerate(regions):
                region_idx = region_indices.get(region, 0)
                
                # Combine shocks
                total_shock = (
                    national_shock + 
                    regional_shocks[region_idx] * correlation_factor +
                    np.random.normal(0, volatility[i] / 100) * uncertainty_factor
                )
                
                # Apply shock to probability (logit space for better behavior)
                logit_prob = np.log(sim_probs[i] / (1 - sim_probs[i]))
                logit_prob += total_shock * 5  # Scale shock
                sim_probs[i] = 1 / (1 + np.exp(-logit_prob))
            
            # Ensure probabilities stay in bounds
            sim_probs = np.clip(sim_probs, 0.001, 0.999)
            
            # Simulate election outcomes
            wins = np.random.random(n_constituencies) < sim_probs
            constituency_wins.append(wins.astype(int))
            nda_seats.append(wins.sum())
        
        return {
            'nda_seats': nda_seats,
            'constituency_wins': constituency_wins
        }
    
    def _calculate_simulation_statistics(self, results: Dict) -> Dict:
        """Calculate comprehensive statistics from simulation results"""
        nda_seats = results['nda_seats']
        constituency_wins = np.array(results['constituency_wins'])
        
        # Basic statistics
        stats = {
            'mean_nda_seats': float(np.mean(nda_seats)),
            'median_nda_seats': float(np.median(nda_seats)),
            'std_nda_seats': float(np.std(nda_seats)),
            'min_nda_seats': int(np.min(nda_seats)),
            'max_nda_seats': int(np.max(nda_seats))
        }
        
        # Percentiles
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        for p in percentiles:
            stats[f'p{p}_nda_seats'] = float(np.percentile(nda_seats, p))
        
        # Probability of different outcomes
        stats['prob_nda_majority'] = float(np.mean(nda_seats >= 122))
        stats['prob_nda_supermajority'] = float(np.mean(nda_seats >= 163))  # 2/3 majority
        stats['prob_nda_strong_majority'] = float(np.mean(nda_seats >= 140))
        stats['prob_hung_assembly'] = float(np.mean((nda_seats >= 110) & (nda_seats < 134)))
        
        # Constituency-level statistics
        constituency_win_probs = np.mean(constituency_wins, axis=0)
        stats['constituency_win_probabilities'] = constituency_win_probs.tolist()
        
        # Seat classification
        stats['safe_nda_seats'] = int(np.sum(constituency_win_probs > 0.8))
        stats['likely_nda_seats'] = int(np.sum((constituency_win_probs > 0.6) & (constituency_win_probs <= 0.8)))
        stats['lean_nda_seats'] = int(np.sum((constituency_win_probs > 0.5) & (constituency_win_probs <= 0.6)))
        stats['toss_up_seats'] = int(np.sum((constituency_win_probs >= 0.4) & (constituency_win_probs <= 0.6)))
        stats['lean_indi_seats'] = int(np.sum((constituency_win_probs >= 0.4) & (constituency_win_probs < 0.5)))
        stats['likely_indi_seats'] = int(np.sum((constituency_win_probs >= 0.2) & (constituency_win_probs < 0.4)))
        stats['safe_indi_seats'] = int(np.sum(constituency_win_probs < 0.2))
        
        # Regional analysis
        if 'region' in self.features_df.columns:
            regional_stats = {}
            for region in self.features_df['region'].unique():
                region_mask = self.features_df['region'] == region
                region_probs = constituency_win_probs[region_mask]
                
                regional_stats[region] = {
                    'total_seats': int(region_mask.sum()),
                    'expected_nda_seats': float(region_probs.sum()),
                    'avg_win_prob': float(region_probs.mean()),
                    'competitive_seats': int(np.sum((region_probs >= 0.4) & (region_probs <= 0.6)))
                }
            
            stats['regional_analysis'] = regional_stats
        
        return stats
    
    def analyze_scenarios(self, results: Dict) -> Dict:
        """Analyze different electoral scenarios"""
        nda_seats = results['simulation_results']['nda_seats']
        
        scenarios = {
            'nda_landslide': {'threshold': 180, 'probability': float(np.mean(nda_seats >= 180))},
            'nda_comfortable': {'threshold': 150, 'probability': float(np.mean(nda_seats >= 150))},
            'nda_majority': {'threshold': 122, 'probability': float(np.mean(nda_seats >= 122))},
            'hung_assembly': {'threshold_low': 110, 'threshold_high': 134, 
                            'probability': float(np.mean((nda_seats >= 110) & (nda_seats < 134)))},
            'indi_majority': {'threshold': 122, 'probability': float(np.mean(nda_seats < 122))},
            'indi_comfortable': {'threshold': 93, 'probability': float(np.mean(nda_seats <= 93))},
            'indi_landslide': {'threshold': 63, 'probability': float(np.mean(nda_seats <= 63))}
        }
        
        # Find most likely scenario
        most_likely = max(scenarios.keys(), key=lambda k: scenarios[k]['probability'])
        
        return {
            'scenarios': scenarios,
            'most_likely_scenario': most_likely,
            'most_likely_probability': scenarios[most_likely]['probability']
        }
    
    def get_marginal_seats(self, results: Dict, threshold: float = 0.1) -> pd.DataFrame:
        """Identify most marginal/competitive seats"""
        constituency_probs = results['statistics']['constituency_win_probabilities']
        
        # Calculate competitiveness (distance from 50%)
        competitiveness = np.abs(np.array(constituency_probs) - 0.5)
        
        # Create marginal seats dataframe
        marginal_df = self.features_df[['constituency', 'region']].copy()
        marginal_df['nda_win_prob'] = constituency_probs
        marginal_df['competitiveness'] = competitiveness
        marginal_df['classification'] = pd.cut(
            marginal_df['nda_win_prob'],
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=['Safe INDI', 'Likely INDI', 'Toss-up', 'Likely NDA', 'Safe NDA']
        )
        
        # Sort by competitiveness (most competitive first)
        marginal_df = marginal_df.sort_values('competitiveness')
        
        # Filter for truly marginal seats
        marginal_seats = marginal_df[marginal_df['competitiveness'] <= threshold]
        
        return marginal_seats
    
    def sensitivity_analysis(self, base_results: Dict, factors: List[str] = None) -> Dict:
        """Perform sensitivity analysis on key factors"""
        if factors is None:
            factors = ['uncertainty', 'correlation', 'national_swing']
        
        sensitivity_results = {}
        
        for factor in factors:
            print(f"   Analyzing sensitivity to {factor}...")
            
            if factor == 'uncertainty':
                # Test different uncertainty levels
                uncertainty_levels = [0.5, 0.75, 1.0, 1.25, 1.5]
                factor_results = []
                
                for level in uncertainty_levels:
                    results = self.run_simulations(n_sims=1000, uncertainty_factor=level)
                    factor_results.append({
                        'level': level,
                        'mean_seats': results['statistics']['mean_nda_seats'],
                        'prob_majority': results['statistics']['prob_nda_majority']
                    })
                
                sensitivity_results[factor] = factor_results
            
            elif factor == 'correlation':
                # Test different correlation levels
                correlation_levels = [0.0, 0.15, 0.3, 0.45, 0.6]
                factor_results = []
                
                for level in correlation_levels:
                    results = self.run_simulations(n_sims=1000, correlation_factor=level)
                    factor_results.append({
                        'level': level,
                        'mean_seats': results['statistics']['mean_nda_seats'],
                        'prob_majority': results['statistics']['prob_nda_majority']
                    })
                
                sensitivity_results[factor] = factor_results
            
            elif factor == 'national_swing':
                # Test different national swing scenarios
                swing_levels = [-3, -2, -1, 0, 1, 2, 3]  # Percentage points
                factor_results = []
                
                for swing in swing_levels:
                    # Adjust base probabilities
                    adjusted_probs = self.base_probs.copy()
                    logit_probs = np.log(adjusted_probs / (1 - adjusted_probs))
                    logit_probs += swing / 10  # Convert to logit scale
                    adjusted_probs = 1 / (1 + np.exp(-logit_probs))
                    adjusted_probs = np.clip(adjusted_probs, 0.01, 0.99)
                    
                    # Temporarily update base probs
                    original_probs = self.base_probs.copy()
                    self.base_probs = adjusted_probs
                    
                    results = self.run_simulations(n_sims=1000)
                    factor_results.append({
                        'level': swing,
                        'mean_seats': results['statistics']['mean_nda_seats'],
                        'prob_majority': results['statistics']['prob_nda_majority']
                    })
                    
                    # Restore original probabilities
                    self.base_probs = original_probs
                
                sensitivity_results[factor] = factor_results
        
        return sensitivity_results
    
    def export_results(self, results: Dict, output_dir: str = None) -> Dict[str, str]:
        """Export simulation results to files"""
        if output_dir is None:
            output_dir = Config.RESULTS_DIR / datetime.now().strftime('%Y-%m-%d')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export summary statistics
        summary_file = output_path / "simulation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results['statistics'], f, indent=2)
        exported_files['summary'] = str(summary_file)
        
        # Export marginal seats
        marginal_seats = self.get_marginal_seats(results)
        marginal_file = output_path / "marginal_seats.csv"
        marginal_seats.to_csv(marginal_file, index=False)
        exported_files['marginal_seats'] = str(marginal_file)
        
        # Export constituency probabilities
        const_probs_df = self.features_df[['constituency', 'region']].copy()
        const_probs_df['nda_win_probability'] = results['statistics']['constituency_win_probabilities']
        const_file = output_path / "constituency_probabilities.csv"
        const_probs_df.to_csv(const_file, index=False)
        exported_files['constituency_probabilities'] = str(const_file)
        
        # Export raw simulation data (sample)
        sample_size = min(1000, len(results['simulation_results']['nda_seats']))
        sample_data = {
            'nda_seats': results['simulation_results']['nda_seats'][:sample_size].tolist(),
            'metadata': results['metadata']
        }
        raw_file = output_path / "simulation_sample.json"
        with open(raw_file, 'w') as f:
            json.dump(sample_data, f, indent=2, default=str)
        exported_files['simulation_sample'] = str(raw_file)
        
        print(f"✅ Exported simulation results to {output_path}")
        return exported_files