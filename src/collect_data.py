#!/usr/bin/env python3
"""
System Resource Tax Investigation - Data Collection Script

This script collects real-time OS performance telemetry to investigate
the "System Resource Tax" - the hidden performance cost that background
processes impose on system performance.

Usage:
    python src/collect_data.py --app-foreground "Code" --app-background "Spotify" --output data/baseline_log.csv
"""

import argparse
import sys
import time
import signal
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import psutil


class SystemMonitor:
    """Monitors system and application resource usage."""
    
    def __init__(self, foreground_app: str, background_app: str, interval: float = 2.0):
        """
        Initialize the system monitor.
        
        Args:
            foreground_app: Name of foreground application (e.g., "Code" for VS Code)
            background_app: Name of background application (e.g., "Spotify")
            interval: Sampling interval in seconds (default: 2.0)
        """
        self.foreground_app = foreground_app.lower()
        self.background_app = background_app.lower()
        self.interval = interval
        self.snapshots: List[Dict] = []
        self.running = True
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        psutil.cpu_percent(interval=0.1)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        print("\n\nShutting down gracefully...")
        self.running = False
    
    def _find_processes_by_name(self, app_name: str) -> List[psutil.Process]:
        """
        Find all processes matching the given application name.
        
        Args:
            app_name: Application name to search for (case-insensitive)
            
        Returns:
            List of matching Process objects
        """
        matching_processes = []
        app_name_lower = app_name.lower()
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if app_name_lower in proc_name:
                    matching_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return matching_processes
    
    def _aggregate_process_metrics(self, processes: List[psutil.Process]) -> Tuple[float, float]:
        """
        Aggregate CPU and memory usage across multiple processes.
        
        Args:
            processes: List of Process objects
            
        Returns:
            Tuple of (total_cpu_percent, total_memory_percent)
        """
        if not processes:
            return 0.0, 0.0
        
        total_cpu = 0.0
        total_memory = 0.0
        
        for proc in processes:
            try:
                cpu_percent = proc.cpu_percent(interval=None)
                memory_info = proc.memory_info()
                memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
                
                total_cpu += cpu_percent
                total_memory += memory_percent
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return total_cpu, total_memory
    
    def _collect_snapshot(self) -> Dict:
        """
        Collect a single snapshot of system and application metrics.
        
        Returns:
            Dictionary containing all collected metrics
        """
        timestamp = datetime.now()
        
        total_system_cpu = psutil.cpu_percent(interval=None)
        total_system_memory = psutil.virtual_memory().percent
        
        net_io = psutil.net_io_counters()
        network_bytes_sent = net_io.bytes_sent
        network_bytes_recv = net_io.bytes_recv
        
        foreground_procs = self._find_processes_by_name(self.foreground_app)
        app_A_cpu, app_A_memory = self._aggregate_process_metrics(foreground_procs)
        
        background_procs = self._find_processes_by_name(self.background_app)
        app_B_cpu, app_B_memory = self._aggregate_process_metrics(background_procs)
        
        snapshot = {
            'timestamp': timestamp,
            'total_system_cpu_percent': total_system_cpu,
            'total_system_memory_percent': total_system_memory,
            'network_bytes_sent': network_bytes_sent,
            'network_bytes_recv': network_bytes_recv,
            'app_A_cpu_percent': app_A_cpu,
            'app_A_memory_percent': app_A_memory,
            'app_B_cpu_percent': app_B_cpu,
            'app_B_memory_percent': app_B_memory,
        }
        
        return snapshot
    
    def run(self, output_path: str):
        """
        Run the monitoring loop and save data to CSV.
        
        Args:
            output_path: Path to save the CSV file
        """
        print(f"Starting data collection...")
        print(f"Foreground app: {self.foreground_app}")
        print(f"Background app: {self.background_app}")
        print(f"Sampling interval: {self.interval} seconds")
        print(f"Output file: {output_path}")
        print(f"\nPress Ctrl+C to stop collection and save data...\n")
        
        try:
            while self.running:
                snapshot = self._collect_snapshot()
                self.snapshots.append(snapshot)
                
                if len(self.snapshots) % 10 == 0:
                    print(f"Collected {len(self.snapshots)} samples... "
                          f"(System CPU: {snapshot['total_system_cpu_percent']:.1f}%)")
                
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            self.running = False
        
        if self.snapshots:
            print(f"\nSaving {len(self.snapshots)} snapshots to {output_path}...")
            df = pd.DataFrame(self.snapshots)
            df.to_csv(output_path, index=False)
            print(f"Data saved successfully!")
            print(f"Total samples: {len(self.snapshots)}")
            print(f"Duration: {len(self.snapshots) * self.interval / 60:.1f} minutes")
        else:
            print("\nNo data collected. Exiting.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect system performance telemetry for System Resource Tax investigation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Baseline condition (30 min, Spotify closed)
  python src/collect_data.py --app-foreground "Code" --app-background "Spotify" --output data/baseline_log.csv

  # Treatment condition (30 min, Spotify streaming)
  python src/collect_data.py --app-foreground "Code" --app-background "Spotify" --output data/treatment_log.csv
        """
    )
    
    parser.add_argument(
        '--app-foreground',
        required=True,
        help='Name of foreground application (e.g., "Code" for VS Code)'
    )
    
    parser.add_argument(
        '--app-background',
        required=True,
        help='Name of background application (e.g., "Spotify")'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output CSV file path (e.g., data/baseline_log.csv)'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=2.0,
        help='Sampling interval in seconds (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(
        foreground_app=args.app_foreground,
        background_app=args.app_background,
        interval=args.interval
    )
    
    monitor.run(args.output)


if __name__ == '__main__':
    main()

