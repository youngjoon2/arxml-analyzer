"""CLI entry point for ARXML Universal Analyzer."""

import click
from pathlib import Path
from typing import Optional, List
import sys
import json
from rich.console import Console
import lxml.etree as ET

from arxml_analyzer.core.parser.xml_parser import XMLParser
from arxml_analyzer.core.parser.stream_parser import StreamParser
from arxml_analyzer.core.analyzer.type_detector import TypeDetector
from arxml_analyzer.analyzers.ecuc_analyzer import ECUCAnalyzer
from arxml_analyzer.core.reporter.formatters import (
    JSONFormatter, 
    TreeFormatter,
    YAMLFormatter,
    TableFormatter,
    CSVFormatter,
    FormatterOptions
)
from arxml_analyzer.core.validator import (
    CompositeValidator,
    ValidationLevel
)
from arxml_analyzer.core.comparator import ARXMLComparator, DifferenceType
from arxml_analyzer.utils.exceptions import ARXMLAnalyzerError

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="arxml-analyzer")
def cli():
    """ARXML Universal Analyzer - Comprehensive ARXML file analysis tool."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o",
    type=click.Choice(["json", "tree", "yaml", "table", "csv"], case_sensitive=False),
    default="tree",
    help="Output format (default: tree)"
)
@click.option(
    "--output-file", "-f",
    type=click.Path(path_type=Path),
    help="Save output to file"
)
@click.option(
    "--stream/--no-stream",
    default=False,
    help="Use streaming parser for large files"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Verbose output"
)
@click.option(
    "--no-metadata",
    is_flag=True,
    help="Exclude metadata from output"
)
@click.option(
    "--no-details",
    is_flag=True,
    help="Exclude details from output"
)
@click.option(
    "--no-patterns",
    is_flag=True,
    help="Exclude patterns from output"
)
@click.option(
    "--no-statistics",
    is_flag=True,
    help="Exclude statistics from output"
)
@click.option(
    "--no-recommendations",
    is_flag=True,
    help="Exclude recommendations from output"
)
@click.option(
    "--analyzer-type",
    type=click.Choice(["auto", "ecuc", "swc", "interface", "gateway"], case_sensitive=False),
    default="auto",
    help="Force specific analyzer type (default: auto-detect)"
)
def analyze(
    file_path: Path,
    output: str,
    output_file: Optional[Path],
    stream: bool,
    verbose: bool,
    no_metadata: bool,
    no_details: bool,
    no_patterns: bool,
    no_statistics: bool,
    no_recommendations: bool,
    analyzer_type: str
):
    """Analyze ARXML file and display results.
    
    FILE_PATH: Path to the ARXML file to analyze
    """
    try:
        # Show analysis start message
        if verbose:
            console.print(f"[cyan]Analyzing file:[/cyan] {file_path}")
            console.print(f"[cyan]File size:[/cyan] {file_path.stat().st_size:,} bytes")
        
        # Select parser based on file size or user preference
        if stream or file_path.stat().st_size > 100_000_000:  # 100MB threshold
            if verbose:
                console.print("[yellow]Using streaming parser for large file[/yellow]")
            parser = StreamParser()
        else:
            parser = XMLParser()
        
        # Parse the file
        with console.status("[bold green]Parsing ARXML file...") if not verbose else console.status(""):
            document = parser.parse(str(file_path))
        
        if verbose:
            console.print("[green]✓[/green] Parsing completed")
        
        # Detect or use specified analyzer type
        if analyzer_type == "auto":
            with console.status("[bold green]Detecting ARXML type...") if not verbose else console.status(""):
                detector = TypeDetector()
                detected_types = detector.detect(document)
            
            if not detected_types:
                console.print("[red]Error:[/red] Could not detect ARXML type", style="bold red")
                sys.exit(1)
            
            # Use the type with highest confidence
            primary_type = detected_types[0].name
            confidence = detected_types[0].confidence
            
            if verbose:
                console.print(f"[green]✓[/green] Detected type: {primary_type} (confidence: {confidence:.1%})")
        else:
            primary_type = analyzer_type.upper()
            if verbose:
                console.print(f"[cyan]Using specified analyzer:[/cyan] {primary_type}")
        
        # Select appropriate analyzer
        analyzer = None
        if primary_type == "ECUC":
            analyzer = ECUCAnalyzer()
        else:
            console.print(f"[yellow]Warning:[/yellow] Analyzer for type '{primary_type}' not yet implemented")
            console.print("[yellow]Falling back to ECUC analyzer for demonstration[/yellow]")
            analyzer = ECUCAnalyzer()
        
        # Run analysis
        with console.status("[bold green]Running analysis...") if not verbose else console.status(""):
            result = analyzer.analyze_safe(document)
        
        if verbose:
            console.print("[green]✓[/green] Analysis completed")
        
        # Prepare formatter options
        formatter_options = FormatterOptions(
            include_metadata=not no_metadata,
            include_details=not no_details,
            include_patterns=not no_patterns,
            include_statistics=not no_statistics,
            include_recommendations=not no_recommendations,
            verbose=verbose,
            color=True
        )
        
        # Format and display results
        output_lower = output.lower()
        if output_lower == "json":
            formatter = JSONFormatter(formatter_options)
        elif output_lower == "yaml":
            formatter = YAMLFormatter(formatter_options)
        elif output_lower == "table":
            formatter = TableFormatter(formatter_options)
        elif output_lower == "csv":
            formatter = CSVFormatter(formatter_options)
        else:  # tree
            formatter = TreeFormatter(formatter_options)
        
        formatted_output = formatter.format(result)
        
        # Output to file or console
        if output_file:
            output_file.write_text(formatted_output, encoding='utf-8')
            console.print(f"[green]✓[/green] Results saved to: {output_file}")
        else:
            console.print(formatted_output)
        
    except ARXMLAnalyzerError as e:
        console.print(f"[red]Analysis Error:[/red] {e}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--schema", type=click.Path(exists=True, path_type=Path), help="XSD schema file path")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def validate(file_path: Path, schema: Optional[Path], output: str, verbose: bool, strict: bool):
    """Validate ARXML file structure and content.
    
    FILE_PATH: Path to the ARXML file to validate
    """
    try:
        # Show validation start message
        if verbose:
            console.print(f"[cyan]Validating file:[/cyan] {file_path}")
            console.print(f"[cyan]File size:[/cyan] {file_path.stat().st_size:,} bytes")
            if schema:
                console.print(f"[cyan]Using schema:[/cyan] {schema}")
        
        # Parse the file
        parser = XMLParser()
        with console.status("[bold green]Parsing ARXML file...") if not verbose else console.status(""):
            document = parser.parse(str(file_path))
        
        if verbose:
            console.print("[green]✓[/green] Parsing completed")
        
        # Create composite validator
        validator = CompositeValidator(schema_path=schema)
        
        # Run validation
        with console.status("[bold green]Running validation...") if not verbose else console.status(""):
            result = validator.validate_safe(document)
        
        if verbose:
            console.print(f"[green]✓[/green] Validation completed in {result.duration:.2f}s")
        
        # Display results
        if output == "json":
            # JSON output
            json_output = {
                "valid": result.is_valid,
                "summary": {
                    "errors": result.error_count,
                    "warnings": result.warning_count,
                    "info": result.info_count,
                    "total": len(result.issues)
                },
                "statistics": result.statistics,
                "issues": [
                    {
                        "level": issue.level.value,
                        "type": issue.type.value,
                        "message": issue.message,
                        "element_path": issue.element_path,
                        "line": issue.line_number,
                        "column": issue.column_number,
                        "rule_id": issue.rule_id,
                        "suggestion": issue.suggestion,
                        "details": issue.details
                    }
                    for issue in result.issues
                ],
                "metadata": result.metadata
            }
            console.print(json.dumps(json_output, indent=2))
        else:
            # Text output
            if result.is_valid:
                console.print("\n[bold green]✓ VALIDATION PASSED[/bold green]")
            else:
                console.print("\n[bold red]✗ VALIDATION FAILED[/bold red]")
            
            # Summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  • Errors:   [red]{result.error_count}[/red]")
            console.print(f"  • Warnings: [yellow]{result.warning_count}[/yellow]")
            console.print(f"  • Info:     [cyan]{result.info_count}[/cyan]")
            console.print(f"  • Total:    {len(result.issues)}")
            
            # Validator statistics
            if verbose and "by_validator" in result.statistics:
                console.print("\n[bold]Validators Run:[/bold]")
                for validator_name, stats in result.statistics["by_validator"].items():
                    if "error" in stats:
                        console.print(f"  • {validator_name}: [red]Failed - {stats['error']}[/red]")
                    else:
                        console.print(f"  • {validator_name}: {stats['issues']} issues")
            
            # Show issues grouped by level
            if result.issues:
                console.print("\n[bold]Issues:[/bold]")
                
                # Group issues by level
                errors = [i for i in result.issues if i.level == ValidationLevel.ERROR]
                warnings = [i for i in result.issues if i.level == ValidationLevel.WARNING]
                info = [i for i in result.issues if i.level == ValidationLevel.INFO]
                
                # Show errors
                if errors:
                    console.print("\n[bold red]Errors:[/bold red]")
                    for idx, issue in enumerate(errors[:10], 1):  # Show first 10
                        console.print(f"  {idx}. {issue.message}")
                        if issue.element_path:
                            console.print(f"     Path: {issue.element_path}")
                        if issue.suggestion:
                            console.print(f"     [dim]Suggestion: {issue.suggestion}[/dim]")
                    if len(errors) > 10:
                        console.print(f"  ... and {len(errors) - 10} more errors")
                
                # Show warnings (if not in strict mode or no errors)
                if warnings and (not strict or not errors):
                    console.print("\n[bold yellow]Warnings:[/bold yellow]")
                    for idx, issue in enumerate(warnings[:5], 1):  # Show first 5
                        console.print(f"  {idx}. {issue.message}")
                        if issue.suggestion:
                            console.print(f"     [dim]Suggestion: {issue.suggestion}[/dim]")
                    if len(warnings) > 5:
                        console.print(f"  ... and {len(warnings) - 5} more warnings")
                
                # Show info messages only in verbose mode
                if info and verbose:
                    console.print("\n[bold cyan]Information:[/bold cyan]")
                    for idx, issue in enumerate(info[:3], 1):  # Show first 3
                        console.print(f"  {idx}. {issue.message}")
                    if len(info) > 3:
                        console.print(f"  ... and {len(info) - 3} more info messages")
        
        # Exit with appropriate code
        if strict and result.warning_count > 0:
            sys.exit(1)
        elif not result.is_valid:
            sys.exit(1)
            
    except ARXMLAnalyzerError as e:
        console.print(f"[red]Validation Error:[/red] {e}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("file1", type=click.Path(exists=True, path_type=Path))
@click.argument("file2", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--ignore-order", is_flag=True, help="Ignore element order")
@click.option("--limit", type=int, default=20, help="Maximum differences to show")
def compare(file1: Path, file2: Path, output: str, verbose: bool, ignore_order: bool, limit: int):
    """Compare two ARXML files and show differences.
    
    FILE1: First ARXML file
    FILE2: Second ARXML file
    """
    try:
        # Show comparison start message
        if verbose:
            console.print(f"[cyan]Comparing files:[/cyan]")
            console.print(f"  File 1: {file1} ({file1.stat().st_size:,} bytes)")
            console.print(f"  File 2: {file2} ({file2.stat().st_size:,} bytes)")
        
        # Parse both files
        parser = XMLParser()
        
        with console.status("[bold green]Parsing first file...") if not verbose else console.status(""):
            doc1 = parser.parse(str(file1))
        
        with console.status("[bold green]Parsing second file...") if not verbose else console.status(""):
            doc2 = parser.parse(str(file2))
        
        if verbose:
            console.print("[green]✓[/green] Files parsed successfully")
        
        # Create comparator and compare
        comparator = ARXMLComparator(ignore_order=ignore_order)
        
        with console.status("[bold green]Comparing files...") if not verbose else console.status(""):
            result = comparator.compare(doc1, doc2)
        
        if verbose:
            console.print("[green]✓[/green] Comparison completed")
        
        # Display results
        if output == "json":
            # JSON output
            json_output = {
                "file1": str(file1),
                "file2": str(file2),
                "identical": result.is_identical,
                "summary": {
                    "total_differences": result.total_differences,
                    "added": len(result.added_elements),
                    "removed": len(result.removed_elements),
                    "modified": len(result.modified_elements),
                    "moved": len(result.moved_elements)
                },
                "differences": {
                    "added": [
                        {
                            "path": diff.path,
                            "details": diff.details
                        }
                        for diff in result.added_elements[:limit]
                    ],
                    "removed": [
                        {
                            "path": diff.path,
                            "details": diff.details
                        }
                        for diff in result.removed_elements[:limit]
                    ],
                    "modified": [
                        {
                            "path": diff.path,
                            "changes": diff.details
                        }
                        for diff in result.modified_elements[:limit]
                    ],
                    "moved": [
                        {
                            "old_path": diff.details.get("old_path"),
                            "new_path": diff.details.get("new_path")
                        }
                        for diff in result.moved_elements[:limit]
                    ]
                },
                "statistics": result.statistics
            }
            console.print(json.dumps(json_output, indent=2))
        else:
            # Text output
            if result.is_identical:
                console.print("\n[bold green]✓ FILES ARE IDENTICAL[/bold green]")
            else:
                console.print(f"\n[bold yellow]⚠ FILES DIFFER[/bold yellow]")
                console.print(f"Total differences: {result.total_differences}")
            
            # Summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  • Added:    [green]+{len(result.added_elements)}[/green]")
            console.print(f"  • Removed:  [red]-{len(result.removed_elements)}[/red]")
            console.print(f"  • Modified: [yellow]~{len(result.modified_elements)}[/yellow]")
            console.print(f"  • Moved:    [cyan]→{len(result.moved_elements)}[/cyan]")
            
            if verbose:
                console.print("\n[bold]Statistics:[/bold]")
                console.print(f"  • File 1 elements: {result.statistics['file1_elements']}")
                console.print(f"  • File 2 elements: {result.statistics['file2_elements']}")
                console.print(f"  • Common elements: {result.statistics['common_elements']}")
            
            # Show differences
            if result.total_differences > 0:
                console.print("\n[bold]Differences:[/bold]")
                
                # Added elements
                if result.added_elements:
                    console.print(f"\n[bold green]Added Elements:[/bold green] (showing {min(limit, len(result.added_elements))} of {len(result.added_elements)})")
                    for diff in result.added_elements[:limit]:
                        console.print(f"  [green]+[/green] {diff.path}")
                        if verbose and diff.details:
                            for key, value in diff.details.items():
                                console.print(f"      {key}: {value}")
                
                # Removed elements
                if result.removed_elements:
                    console.print(f"\n[bold red]Removed Elements:[/bold red] (showing {min(limit, len(result.removed_elements))} of {len(result.removed_elements)})")
                    for diff in result.removed_elements[:limit]:
                        console.print(f"  [red]-[/red] {diff.path}")
                        if verbose and diff.details:
                            for key, value in diff.details.items():
                                console.print(f"      {key}: {value}")
                
                # Modified elements
                if result.modified_elements:
                    console.print(f"\n[bold yellow]Modified Elements:[/bold yellow] (showing {min(limit, len(result.modified_elements))} of {len(result.modified_elements)})")
                    for diff in result.modified_elements[:limit]:
                        console.print(f"  [yellow]~[/yellow] {diff.path}")
                        if diff.details:
                            for key, value in diff.details.items():
                                if isinstance(value, dict) and 'old' in value and 'new' in value:
                                    console.print(f"      {key}: {value['old']} → {value['new']}")
                                else:
                                    console.print(f"      {key}: {value}")
                
                # Moved elements
                if result.moved_elements:
                    console.print(f"\n[bold cyan]Moved Elements:[/bold cyan] (showing {min(limit, len(result.moved_elements))} of {len(result.moved_elements)})")
                    for diff in result.moved_elements[:limit]:
                        old_path = diff.details.get("old_path", "?")
                        new_path = diff.details.get("new_path", diff.path)
                        console.print(f"  [cyan]→[/cyan] {old_path} → {new_path}")
        
        # Exit with appropriate code
        if not result.is_identical:
            sys.exit(1)
            
    except ARXMLAnalyzerError as e:
        console.print(f"[red]Comparison Error:[/red] {e}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def stats(file_path: Path, format: str, verbose: bool):
    """Display statistics about ARXML file.
    
    FILE_PATH: Path to the ARXML file
    """
    try:
        from rich.table import Table
        from collections import Counter
        
        # Show processing message
        if verbose:
            console.print(f"[cyan]Analyzing file:[/cyan] {file_path}")
            console.print(f"[cyan]File size:[/cyan] {file_path.stat().st_size:,} bytes")
        
        # Parse the file
        parser = XMLParser()
        with console.status("[bold green]Parsing ARXML file...") if not verbose else console.status(""):
            document = parser.parse(str(file_path))
        
        if verbose:
            console.print("[green]✓[/green] Parsing completed")
        
        # Collect statistics
        with console.status("[bold green]Collecting statistics...") if not verbose else console.status(""):
            stats_data = {}
            
            # Basic file info
            stats_data["file_info"] = {
                "path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # AUTOSAR info
            stats_data["autosar"] = {
                "version": document.get_autosar_version() or "Unknown",
                "namespaces": list(document.namespaces.keys()) if document.namespaces else []
            }
            
            # Element counts
            all_elements = document.root.xpath(".//*")
            element_counter = Counter()
            for elem in all_elements:
                if hasattr(elem, 'tag'):
                    tag = elem.tag
                    if isinstance(tag, str):
                        local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                        element_counter[local_name] += 1
            
            stats_data["elements"] = {
                "total_count": len(all_elements),
                "unique_types": len(element_counter),
                "top_10": dict(element_counter.most_common(10))
            }
            
            # Package structure
            packages = []
            for pkg in document.root.xpath(".//*"):
                if hasattr(pkg, 'tag'):
                    tag = pkg.tag
                    if isinstance(tag, str):
                        local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                        if local_name == "AR-PACKAGE":
                            # Find SHORT-NAME
                            for child in pkg:
                                if hasattr(child, 'tag'):
                                    child_tag = child.tag
                                    if isinstance(child_tag, str):
                                        child_local = ET.QName(child_tag).localname if child_tag.startswith('{') else child_tag
                                        if child_local == "SHORT-NAME" and child.text:
                                            packages.append(child.text)
                                            break
            
            stats_data["packages"] = {
                "count": len(packages),
                "names": packages[:10]  # First 10 packages
            }
            
            # Detect document type
            detector = TypeDetector()
            detected_types = detector.detect(document)
            stats_data["document_types"] = [
                {
                    "type": dt.name,
                    "confidence": round(dt.confidence * 100, 1)
                }
                for dt in detected_types[:3]  # Top 3 types
            ]
            
            # Special elements
            special_counts = {
                "SHORT-NAME": element_counter.get("SHORT-NAME", 0),
                "DEFINITION-REF": element_counter.get("DEFINITION-REF", 0),
                "ECUC-MODULE-CONFIGURATION-VALUES": element_counter.get("ECUC-MODULE-CONFIGURATION-VALUES", 0),
                "APPLICATION-SW-COMPONENT-TYPE": element_counter.get("APPLICATION-SW-COMPONENT-TYPE", 0),
                "SENDER-RECEIVER-INTERFACE": element_counter.get("SENDER-RECEIVER-INTERFACE", 0),
                "CLIENT-SERVER-INTERFACE": element_counter.get("CLIENT-SERVER-INTERFACE", 0)
            }
            stats_data["special_elements"] = special_counts
            
            # Calculate depth
            def get_max_depth(elem, depth=0):
                children = [c for c in elem if hasattr(c, 'tag')]
                if not children:
                    return depth
                return max(get_max_depth(child, depth + 1) for child in children)
            
            stats_data["structure"] = {
                "max_depth": get_max_depth(document.root),
                "avg_children": round(sum(len([c for c in e if hasattr(c, 'tag')]) 
                                         for e in all_elements) / len(all_elements), 2) if all_elements else 0
            }
        
        if verbose:
            console.print("[green]✓[/green] Statistics collected")
        
        # Display results
        if format == "json":
            # JSON output
            console.print(json.dumps(stats_data, indent=2))
        else:
            # Table output
            console.print("\n[bold]ARXML File Statistics[/bold]\n")
            
            # File info table
            file_table = Table(title="File Information", show_header=True)
            file_table.add_column("Property", style="cyan")
            file_table.add_column("Value", style="white")
            
            file_table.add_row("Path", str(file_path.name))
            file_table.add_row("Size", f"{stats_data['file_info']['size_bytes']:,} bytes ({stats_data['file_info']['size_mb']} MB)")
            file_table.add_row("AUTOSAR Version", stats_data['autosar']['version'])
            
            console.print(file_table)
            
            # Document type table
            if stats_data.get("document_types"):
                console.print()
                type_table = Table(title="Detected Document Types", show_header=True)
                type_table.add_column("Type", style="cyan")
                type_table.add_column("Confidence", style="yellow")
                
                for dt in stats_data["document_types"]:
                    type_table.add_row(dt["type"], f"{dt['confidence']}%")
                
                console.print(type_table)
            
            # Element statistics table
            console.print()
            elem_table = Table(title="Element Statistics", show_header=True)
            elem_table.add_column("Metric", style="cyan")
            elem_table.add_column("Value", style="white")
            
            elem_table.add_row("Total Elements", str(stats_data['elements']['total_count']))
            elem_table.add_row("Unique Element Types", str(stats_data['elements']['unique_types']))
            elem_table.add_row("Maximum Depth", str(stats_data['structure']['max_depth']))
            elem_table.add_row("Average Children per Element", str(stats_data['structure']['avg_children']))
            elem_table.add_row("Packages", str(stats_data['packages']['count']))
            
            console.print(elem_table)
            
            # Top elements table
            console.print()
            top_table = Table(title="Top 10 Most Frequent Elements", show_header=True)
            top_table.add_column("Element", style="cyan")
            top_table.add_column("Count", style="yellow")
            
            for elem_name, count in stats_data['elements']['top_10'].items():
                top_table.add_row(elem_name, str(count))
            
            console.print(top_table)
            
            # Special elements table (if any exist)
            special_with_counts = {k: v for k, v in stats_data['special_elements'].items() if v > 0}
            if special_with_counts:
                console.print()
                special_table = Table(title="Special Elements", show_header=True)
                special_table.add_column("Element Type", style="cyan")
                special_table.add_column("Count", style="yellow")
                
                for elem_name, count in special_with_counts.items():
                    special_table.add_row(elem_name, str(count))
                
                console.print(special_table)
            
            # Package list (if verbose)
            if verbose and stats_data['packages']['names']:
                console.print("\n[bold]Packages:[/bold]")
                for pkg_name in stats_data['packages']['names']:
                    console.print(f"  • {pkg_name}")
                if stats_data['packages']['count'] > 10:
                    console.print(f"  ... and {stats_data['packages']['count'] - 10} more")
        
    except ARXMLAnalyzerError as e:
        console.print(f"[red]Statistics Error:[/red] {e}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()