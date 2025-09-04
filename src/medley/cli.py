#!/usr/bin/env python
"""
Medley CLI - Command line interface for medical AI ensemble analysis
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from typing import Optional

from .utils.config import Config
from .models.llm_manager import LLMManager
from .models.ensemble import EnsembleOrchestrator
from .processors.case_processor import CaseProcessor
from .processors.response_parser import ResponseParser
from .processors.cache_manager import CacheManager
from .reporters.consensus_report import ConsensusReportGenerator
from .reporters.enhanced_report import EnhancedReportGenerator

console = Console()

@click.group()
@click.version_option(version="0.1.0", prog_name="medley", 
                     message="%(prog)s %(version)s\nDeveloped by Farhad Abtahi - SMAILE at Karolinska Institutet\nWebsite: smile.ki.se")
def cli():
    """Medley - Medical AI Ensemble System
    
    A bias-aware multi-model diagnostic framework for medical cases.
    
    Author: Farhad Abtahi
    Institution: SMAILE at Karolinska Institutet
    Website: smile.ki.se
    """
    pass

@cli.command()
@click.argument("case_file", type=click.Path(exists=True))
@click.option("--model", "-m", default="gemini-2.5-pro", help="Model to use for analysis")
@click.option("--no-cache", is_flag=True, help="Skip cache and force new API call")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def analyze(case_file: str, model: str, no_cache: bool, output: Optional[str], output_json: bool):
    """Analyze a medical case using specified model"""
    
    with console.status("[bold green]Initializing Medley...") as status:
        # Initialize components
        try:
            config = Config()
            config.validate()
        except ValueError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            console.print("[yellow]Please set OPENROUTER_API_KEY environment variable[/yellow]")
            sys.exit(1)
        
        llm_manager = LLMManager(config)
        case_processor = CaseProcessor()
        response_parser = ResponseParser()
        cache_manager = CacheManager(config.cache_dir)
        
        # Load case
        status.update("[bold blue]Loading case file...")
        case_path = Path(case_file)
        try:
            medical_case = case_processor.load_case_from_file(case_path)
        except Exception as e:
            console.print(f"[red]Error loading case: {e}[/red]")
            sys.exit(1)
        
        # Get model configuration
        model_config = config.get_model(model)
        if not model_config:
            console.print(f"[red]Model '{model}' not configured[/red]")
            console.print("[yellow]Available models:[/yellow]")
            for m in config.get_all_models():
                console.print(f"  - {m.name}")
            sys.exit(1)
        
        # Prepare prompt
        prompt_template = config.get_prompt("medical_analysis")
        prompt = prompt_template.format(case_content=medical_case.to_prompt())
        
        # Check cache unless disabled
        llm_response = None
        if not no_cache:
            status.update("[bold cyan]Checking cache...")
            llm_response = cache_manager.get_cached_response(
                case_id=medical_case.case_id,
                model_id=model_config.model_id,
                prompt=prompt
            )
            if llm_response:
                console.print("[green]✓ Using cached response[/green]")
        
        # Query model if no cached response
        if not llm_response:
            status.update(f"[bold yellow]Querying {model_config.name}...")
            
            # Test connection first
            if not llm_manager.test_connection():
                console.print("[red]Failed to connect to OpenRouter API[/red]")
                console.print("[yellow]Please check your API key and internet connection[/yellow]")
                sys.exit(1)
            
            llm_response = llm_manager.query_model(model_config, prompt)
            
            if llm_response.error:
                console.print(f"[red]Error from model: {llm_response.error}[/red]")
                sys.exit(1)
            
            # Save to cache
            cache_manager.save_response(
                case_id=medical_case.case_id,
                model_id=model_config.model_id,
                prompt=prompt,
                response=llm_response
            )
            console.print("[green]✓ Response cached[/green]")
        
        # Parse response
        status.update("[bold magenta]Parsing response...")
        parsed_response = response_parser.parse_response(llm_response.content)
    
    # Display results
    if output_json:
        result = {
            "case": medical_case.to_dict(),
            "model": {
                "name": model_config.name,
                "id": model_config.model_id
            },
            "response": parsed_response.to_dict(),
            "metadata": {
                "latency": llm_response.latency,
                "tokens_used": llm_response.tokens_used,
                "timestamp": llm_response.timestamp
            }
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            console.print(f"[green]Results saved to {output}[/green]")
        else:
            console.print_json(json.dumps(result, indent=2, default=str))
    else:
        # Display formatted results
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            f"[bold cyan]Medical Case Analysis[/bold cyan]\n"
            f"Case: {medical_case.case_id}\n"
            f"Model: {model_config.name}",
            border_style="cyan"
        ))
        
        # Initial Impression
        if parsed_response.initial_impression:
            console.print("\n[bold]Initial Impression:[/bold]")
            console.print(parsed_response.initial_impression)
        
        # Differential Diagnoses
        if parsed_response.differential_diagnoses:
            console.print("\n[bold]Differential Diagnoses:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Diagnosis", style="cyan")
            table.add_column("Reasoning", style="white")
            
            for i, diag in enumerate(parsed_response.differential_diagnoses, 1):
                table.add_row(
                    str(i),
                    diag["diagnosis"],
                    diag["reasoning"][:100] + "..." if len(diag["reasoning"]) > 100 else diag["reasoning"]
                )
            
            console.print(table)
        
        # Alternative Perspectives
        if parsed_response.alternative_perspectives:
            console.print("\n[bold]Alternative Perspectives:[/bold]")
            console.print(parsed_response.alternative_perspectives)
        
        # Next Steps
        if parsed_response.next_steps:
            console.print("\n[bold]Next Steps:[/bold]")
            console.print(parsed_response.next_steps)
        
        # Uncertainties
        if parsed_response.uncertainties:
            console.print("\n[bold]Uncertainties:[/bold]")
            console.print(parsed_response.uncertainties)
        
        # Metadata
        console.print("\n[dim]---")
        console.print(f"[dim]Latency: {llm_response.latency:.2f}s | Tokens: {llm_response.tokens_used}[/dim]")
        
        if output:
            with open(output, 'w') as f:
                f.write(f"Medical Case Analysis\n")
                f.write(f"Case: {medical_case.case_id}\n")
                f.write(f"Model: {model_config.name}\n\n")
                f.write(f"Initial Impression:\n{parsed_response.initial_impression}\n\n")
                f.write(f"Full Response:\n{llm_response.content}\n")
            console.print(f"\n[green]Results saved to {output}[/green]")

@cli.command()
def setup():
    """Initialize Medley configuration and directories"""
    
    console.print("[bold cyan]Setting up Medley...[/bold cyan]\n")
    
    # Create configuration
    config = Config()
    
    # Check API key
    if not config.api_key:
        console.print("[yellow]⚠ OpenRouter API key not found[/yellow]")
        console.print("Please set the OPENROUTER_API_KEY environment variable")
        console.print("\nExample:")
        console.print("  export OPENROUTER_API_KEY='your-api-key-here'")
    else:
        console.print("[green]✓ OpenRouter API key configured[/green]")
    
    # Save default configurations
    config.save_default_configs()
    console.print("[green]✓ Default configurations saved[/green]")
    
    # Create directories
    directories = [
        config.cache_dir,
        config.reports_dir,
        config.config_dir,
        Path.cwd() / "usecases"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓ Created directory: {directory}[/green]")
    
    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Add medical cases to the 'usecases' directory")
    console.print("2. Run: medley analyze <case_file>")

@cli.command()
def cache_stats():
    """Display cache statistics"""
    
    config = Config()
    cache_manager = CacheManager(config.cache_dir)
    
    stats = cache_manager.get_cache_statistics()
    
    console.print(Panel.fit(
        "[bold cyan]Cache Statistics[/bold cyan]",
        border_style="cyan"
    ))
    
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Total Cached Responses", str(stats["total_cached_responses"]))
    table.add_row("Unique Cases", str(stats["unique_cases"]))
    table.add_row("Total Tokens Used", f"{stats['total_tokens_used']:,}")
    table.add_row("Average Latency", f"{stats['average_latency']:.2f}s")
    table.add_row("Cache Size", f"{stats['cache_size_mb']:.2f} MB")
    
    console.print(table)
    
    if stats["responses_by_model"]:
        console.print("\n[bold]Responses by Model:[/bold]")
        for model, count in stats["responses_by_model"].items():
            console.print(f"  • {model}: {count}")

@cli.command()
@click.argument("case_id")
def clear_cache(case_id: str):
    """Clear cache for a specific case"""
    
    config = Config()
    cache_manager = CacheManager(config.cache_dir)
    
    cache_manager.clear_case_cache(case_id)
    console.print(f"[green]✓ Cleared cache for case: {case_id}[/green]")

@cli.command()
def validate():
    """Validate cache integrity"""
    
    config = Config()
    cache_manager = CacheManager(config.cache_dir)
    
    result = cache_manager.validate_cache()
    
    if result["valid"]:
        console.print("[green]✓ Cache is valid[/green]")
        console.print(f"Checked {result['checked_entries']} entries")
    else:
        console.print("[red]✗ Cache validation failed[/red]")
        console.print(f"Found {len(result['issues'])} issues:")
        for issue in result["issues"]:
            console.print(f"  • {issue}")

@cli.command()
@click.argument("case_file", type=click.Path(exists=True))
@click.option("--models", "-m", multiple=True, help="Specific models to use (can specify multiple)")
@click.option("--output-dir", "-o", type=click.Path(), help="Directory to save results")
@click.option("--format", type=click.Choice(["markdown", "html", "text", "pdf"]), default="markdown", help="Report format")
@click.option("--no-cache", is_flag=True, help="Skip cache and force new API calls")
@click.option("--use-paid", is_flag=True, help="Include paid models in analysis (default if not --free-only)")
@click.option("--free-only", is_flag=True, help="Use only free models")
@click.option("--max-paid", type=int, default=3, help="Maximum number of paid models to use")
@click.option("--consensus-mode", type=click.Choice(["statistical", "ai-enhanced"]), default="statistical", 
              help="Consensus analysis mode: statistical or AI-enhanced using Gemini")
@click.option("--report-type", type=click.Choice(["standard", "enhanced", "comprehensive"]), default="comprehensive",
              help="Report type: standard (consensus), enhanced (diversity), or comprehensive (full analysis like Case 1-12)")
def ensemble(case_file: str, models: tuple, output_dir: Optional[str], format: str, no_cache: bool, 
             use_paid: bool, free_only: bool, max_paid: int, consensus_mode: str, report_type: str):
    """Run ensemble analysis with multiple models"""
    
    with console.status("[bold green]Initializing Medley Ensemble...") as status:
        # Initialize components
        try:
            config = Config()
            config.validate()
        except ValueError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            console.print("[yellow]Please set OPENROUTER_API_KEY environment variable[/yellow]")
            sys.exit(1)
        
        # Initialize orchestrator
        orchestrator = EnsembleOrchestrator(config)
        
        # Select report generator based on report type
        if report_type == "comprehensive":
            from .reporters.comprehensive_report import ComprehensiveReportGenerator
            report_generator = ComprehensiveReportGenerator()
        elif report_type == "enhanced":
            report_generator = EnhancedReportGenerator()
        else:
            report_generator = ConsensusReportGenerator()
        
        # Prepare models if specified
        model_configs = None
        if models:
            model_configs = []
            for model_name in models:
                model_config = config.get_model(model_name)
                if model_config:
                    model_configs.append({
                        "name": model_config.model_id,
                        "origin": model_config.origin,
                        "size": model_config.size
                    })
                else:
                    console.print(f"[yellow]Warning: Model '{model_name}' not found, skipping[/yellow]")
        
        # Set output directory
        if not output_dir:
            output_dir = config.reports_dir
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Determine whether to use paid models
        use_paid_models = not free_only and use_paid
        
        # Run ensemble analysis
        console.print(f"\n[bold cyan]Running ensemble analysis on: {case_file}[/bold cyan]")
        if free_only:
            console.print("[yellow]Using free models only[/yellow]")
        elif use_paid_models:
            console.print(f"[green]Using both free and paid models (max {max_paid} paid)[/green]")
        
        # Use GeneralMedicalPipeline for better analysis
        import sys as sys_module
        import os
        from pathlib import Path as PathLib
        # Add parent directory to path to import general_medical_pipeline
        sys_module.path.insert(0, str(PathLib(__file__).parent.parent.parent))
        from general_medical_pipeline import GeneralMedicalPipeline
        
        # Extract case ID from filename
        case_path = PathLib(case_file)
        case_id = case_path.stem
        
        # Initialize pipeline
        pipeline = GeneralMedicalPipeline(case_id)
        
        # Read case content
        with open(case_file, 'r') as f:
            case_content = f.read()
        
        # Set environment for model selection
        if free_only:
            os.environ['USE_FREE_MODELS'] = 'true'
        elif use_paid:
            os.environ.pop('USE_FREE_MODELS', None)
        
        # Run analysis using the pipeline
        try:
            pipeline_results = pipeline.run_complete_analysis(
                case_description=case_content,
                case_title=case_id
            )
            
            # Load the generated ensemble data for the report
            if pipeline_results.get('data_file'):
                with open(pipeline_results['data_file'], 'r') as f:
                    results = json.load(f)
            else:
                console.print("[red]Error: No data file generated by pipeline[/red]")
                sys.exit(1)
                
        except Exception as e:
            console.print(f"[red]Error during ensemble analysis: {e}[/red]")
            sys.exit(1)
    
    # Reports are already generated by the pipeline
    console.print("\n[bold magenta]Reports generated by pipeline:[/bold magenta]")
    
    if pipeline_results.get('report_file'):
        console.print(f"[green]✓ PDF report: {pipeline_results['report_file']}[/green]")
    
    if pipeline_results.get('data_file'):
        console.print(f"[green]✓ JSON data: {pipeline_results['data_file']}[/green]")
    
    # Display summary
    consensus = results.get("consensus_analysis", {})
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        f"[bold cyan]Ensemble Analysis Complete[/bold cyan]\n"
        f"Case: {results.get('case_title', 'Unknown')}\n"
        f"Models Analyzed: {results.get('models_queried', 0)}\n"
        f"Successful Responses: {consensus.get('responding_models', 0)}\n"
        f"Consensus Level: {consensus.get('consensus_level', 'None')}",
        border_style="cyan"
    ))
    
    # Display primary diagnosis
    if consensus.get("primary_diagnosis"):
        console.print(f"\n[bold]Primary Diagnosis:[/bold] {consensus['primary_diagnosis']}")
        console.print(f"[bold]Confidence:[/bold] {consensus.get('primary_confidence', 0)*100:.0f}%")
    
    # Display alternatives
    alternatives = consensus.get("alternative_diagnoses", [])
    if alternatives:
        console.print("\n[bold]Alternative Diagnoses:[/bold]")
        for i, alt in enumerate(alternatives[:3], 1):
            console.print(f"  {i}. {alt.get('diagnosis', 'Unknown')} ({alt.get('confidence', 0)*100:.0f}% agreement)")
    
    # Display clinical recommendation
    if consensus.get("clinical_recommendation"):
        console.print(f"\n[bold]Clinical Recommendation:[/bold]")
        console.print(consensus["clinical_recommendation"])
    
    # Display bias considerations
    bias_considerations = consensus.get("bias_considerations", [])
    if bias_considerations:
        console.print("\n[bold yellow]⚠ Bias Considerations:[/bold yellow]")
        for bias in bias_considerations:
            console.print(f"  • {bias}")
    
    console.print("\n[dim]Use 'medley validate' to check cache integrity[/dim]")

@cli.command()
def test():
    """Test OpenRouter API connection"""
    
    try:
        config = Config()
        config.validate()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)
    
    llm_manager = LLMManager(config)
    
    with console.status("[bold green]Testing OpenRouter API connection...") as status:
        if llm_manager.test_connection():
            console.print("[green]✓ Successfully connected to OpenRouter API[/green]")
            
            # Test with a simple query
            status.update("Testing model query...")
            model_config = config.get_all_models()[0]
            response = llm_manager.query_model(
                model_config,
                "Say 'Hello, Medley is working!' in exactly 5 words."
            )
            
            if response.error:
                console.print(f"[yellow]⚠ Model query failed: {response.error}[/yellow]")
            else:
                console.print(f"[green]✓ Model response: {response.content}[/green]")
                console.print(f"[dim]Model: {model_config.name}[/dim]")
                console.print(f"[dim]Latency: {response.latency:.2f}s[/dim]")
        else:
            console.print("[red]✗ Failed to connect to OpenRouter API[/red]")
            console.print("[yellow]Please check your API key and internet connection[/yellow]")

def main():
    """Main entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()