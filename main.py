#!/usr/bin/env python3
"""
Main script for Audio Gran Campaña processing.

This script provides a command-line interface to execute the complete audio
processing pipeline that combines locutor audio files with background music.
"""

import argparse
import sys
from pathlib import Path

from src.audio_processor import AudioProcessor
from src.exceptions import AudioProcessingError, MissingFileError
from src.logger_config import get_logger


logger = get_logger('main')


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Audio Gran Campaña - Automated audio processing system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Use default folders
  python main.py -i files/source -o files/output   # Specify custom folders
  python main.py --input /path/to/audio --output /path/to/results
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='files/source',
        help='Input folder containing audio files (default: files/source)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='files/output',
        help='Output folder for processed audio (default: files/output)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Audio Gran Campaña v1.0.0'
    )
    
    return parser.parse_args()


def validate_folders(input_folder: Path, output_folder: Path) -> None:
    """
    Validate input and output folders.
    
    Args:
        input_folder: Path to input folder
        output_folder: Path to output folder
        
    Raises:
        FileNotFoundError: If input folder doesn't exist
        PermissionError: If output folder can't be created or written to
    """
    # Validate input folder exists
    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
    
    if not input_folder.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_folder}")
    
    # Create output folder if it doesn't exist
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(f"Cannot create output folder: {output_folder}. {e}")
    
    # Test write permissions in output folder
    test_file = output_folder / '.write_test'
    try:
        test_file.touch()
        test_file.unlink()
    except PermissionError as e:
        raise PermissionError(f"Cannot write to output folder: {output_folder}. {e}")


def print_processing_summary(result):
    """Print a summary of the processing results."""
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    if result.success:
        print("✅ Status: SUCCESS")
        print(f"📁 Output file: {result.output_path}")
        print(f"⏱️  Final duration: {result.final_duration_ms/1000:.2f} seconds")
        
        if result.locutor_result:
            print(f"🎤 Locutor files loaded: {len(result.locutor_result.files_loaded)}")
            if result.locutor_result.files_skipped:
                print(f"⚠️  Locutor files skipped: {len(result.locutor_result.files_skipped)}")
        
        if result.background_result:
            print(f"🎵 Background music processed: {result.background_result.crossfade_applied and 'with crossfade' or 'without crossfade'}")
        
        if result.validation_warnings:
            print(f"⚠️  Validation warnings: {len(result.validation_warnings)}")
            for warning in result.validation_warnings:
                print(f"   - {warning}")
    else:
        print("❌ Status: FAILED")
        print(f"💥 Error: {result.error_message}")
    
    print("="*60)


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Convert paths to Path objects
        input_folder = Path(args.input).resolve()
        output_folder = Path(args.output).resolve()
        
        print("🎵 Audio Gran Campaña - Starting audio processing...")
        print(f"📂 Input folder: {input_folder}")
        print(f"📁 Output folder: {output_folder}")
        
        # Validate folders
        logger.info("Validating input and output folders")
        validate_folders(input_folder, output_folder)
        
        # Initialize and run audio processor
        logger.info("Initializing AudioProcessor")
        processor = AudioProcessor(input_folder, output_folder)
        
        print("\n🔄 Processing audio files...")
        result = processor.process()
        
        # Print results summary
        print_processing_summary(result)
        
        # Exit with appropriate code
        if result.success:
            logger.info("Audio processing completed successfully")
            print("\n🎉 Audio processing completed successfully!")
            sys.exit(0)
        else:
            logger.error(f"Audio processing failed: {result.error_message}")
            sys.exit(1)
            
    except MissingFileError as e:
        error_msg = f"Missing required files: {e}"
        logger.error(error_msg)
        print(f"\n❌ Error: {error_msg}")
        print("💡 Make sure all required audio files are in the input folder:")
        print("   - Yo tengo un amigo que me ama.mp3")
        print("   - Eres todo poderoso.mp3")
        print("   - At least one locutor file from the sequence")
        sys.exit(1)
        
    except AudioProcessingError as e:
        error_msg = f"Audio processing error: {e}"
        logger.error(error_msg)
        print(f"\n❌ Error: {error_msg}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        logger.error(error_msg)
        print(f"\n❌ Error: {error_msg}")
        sys.exit(1)
        
    except PermissionError as e:
        error_msg = f"Permission error: {e}"
        logger.error(error_msg)
        print(f"\n❌ Error: {error_msg}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\n⏹️  Processing interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"\n💥 Unexpected error: {error_msg}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == '__main__':
    main()