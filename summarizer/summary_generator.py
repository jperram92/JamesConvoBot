"""
Summary generator for AI Meeting Assistant.
"""
from typing import Any, Dict, List, Optional

from agent_core.llm_manager import get_openai_manager
from summarizer.transcript_processor import TranscriptProcessor
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class SummaryGenerator:
    """Generator for meeting summaries."""
    
    def __init__(self):
        """Initialize the summary generator."""
        self.summary_length = config.get('summarization.summary_length', 'medium')
        self.generate_action_items = config.get('summarization.generate_action_items', True)
        
        # Initialize transcript processor
        self.transcript_processor = TranscriptProcessor()
        
        # Initialize OpenAI manager
        self.openai_manager = get_openai_manager()
        
        logger.info("Initialized summary generator")
    
    def generate_summary(self, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of a meeting transcript.
        
        Args:
            transcript: List of transcript entries.
            
        Returns:
            Dictionary containing summary, action items, and other information.
        """
        try:
            # Process transcript
            transcript_text = self.transcript_processor.process_transcript(transcript)
            
            # Extract speakers
            speakers = self.transcript_processor.extract_speakers(transcript)
            
            # Generate summary
            summary = self._generate_summary_with_llm(transcript_text)
            
            # Extract action items
            action_items = []
            if self.generate_action_items:
                action_items = self._generate_action_items_with_llm(transcript_text)
            
            # Extract key points
            key_points = self._generate_key_points_with_llm(transcript_text)
            
            return {
                "summary": summary,
                "action_items": action_items,
                "key_points": key_points,
                "speakers": speakers,
                "transcript": transcript_text
            }
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "action_items": [],
                "key_points": [],
                "speakers": [],
                "transcript": ""
            }
    
    def _generate_summary_with_llm(self, transcript_text: str) -> str:
        """
        Generate a summary using the LLM.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            Generated summary.
        """
        # Determine max tokens based on summary length
        max_tokens = {
            "short": 150,
            "medium": 300,
            "long": 500
        }.get(self.summary_length, 300)
        
        # Create prompt
        prompt = f"""
        Please summarize the following meeting transcript. 
        Provide a {self.summary_length} summary that captures the main points discussed, 
        decisions made, and the overall purpose of the meeting.
        
        Transcript:
        {transcript_text}
        """
        
        # Generate summary
        response = self.openai_manager.generate_response(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        
        # Extract summary
        summary = response["choices"][0]["message"]["content"]
        
        return summary
    
    def _generate_action_items_with_llm(self, transcript_text: str) -> List[Dict[str, str]]:
        """
        Generate action items using the LLM.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            List of action items.
        """
        # Create prompt
        prompt = f"""
        Please extract action items from the following meeting transcript.
        For each action item, identify the assignee (who is responsible) and the task.
        Format your response as a JSON array of objects, each with "assignee" and "task" fields.
        
        Transcript:
        {transcript_text}
        """
        
        # Generate action items
        response = self.openai_manager.generate_response(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        # Extract action items
        content = response["choices"][0]["message"]["content"]
        
        # Parse JSON
        try:
            import json
            action_items = json.loads(content)
            
            # Validate format
            if not isinstance(action_items, list):
                return []
            
            # Filter out invalid items
            valid_items = []
            for item in action_items:
                if isinstance(item, dict) and "assignee" in item and "task" in item:
                    valid_items.append({
                        "assignee": item["assignee"],
                        "task": item["task"]
                    })
            
            return valid_items
        
        except Exception as e:
            logger.error(f"Error parsing action items: {e}")
            return []
    
    def _generate_key_points_with_llm(self, transcript_text: str) -> List[str]:
        """
        Generate key points using the LLM.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            List of key points.
        """
        # Create prompt
        prompt = f"""
        Please extract the key points from the following meeting transcript.
        Provide a list of the most important points discussed, decisions made, or insights shared.
        Format your response as a JSON array of strings.
        
        Transcript:
        {transcript_text}
        """
        
        # Generate key points
        response = self.openai_manager.generate_response(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        # Extract key points
        content = response["choices"][0]["message"]["content"]
        
        # Parse JSON
        try:
            import json
            key_points = json.loads(content)
            
            # Validate format
            if not isinstance(key_points, list):
                return []
            
            # Filter out invalid items
            valid_points = []
            for point in key_points:
                if isinstance(point, str):
                    valid_points.append(point)
            
            return valid_points
        
        except Exception as e:
            logger.error(f"Error parsing key points: {e}")
            return []
    
    def format_summary_email(self, summary_data: Dict[str, Any]) -> str:
        """
        Format a summary for email.
        
        Args:
            summary_data: Summary data.
            
        Returns:
            Formatted email HTML.
        """
        # Create email HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                .summary {{ margin-bottom: 20px; }}
                .key-points {{ margin-bottom: 20px; }}
                .action-items {{ margin-bottom: 20px; }}
                .action-item {{ margin-bottom: 10px; }}
                .transcript {{ font-size: 0.9em; color: #7f8c8d; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <h1>Meeting Summary</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>{summary_data.get('summary', 'No summary available.')}</p>
            </div>
            
            <div class="key-points">
                <h2>Key Points</h2>
                <ul>
        """
        
        # Add key points
        key_points = summary_data.get('key_points', [])
        if key_points:
            for point in key_points:
                html += f'<li>{point}</li>'
        else:
            html += '<li>No key points identified.</li>'
        
        html += """
                </ul>
            </div>
            
            <div class="action-items">
                <h2>Action Items</h2>
                <ul>
        """
        
        # Add action items
        action_items = summary_data.get('action_items', [])
        if action_items:
            for item in action_items:
                html += f'<li class="action-item"><strong>{item.get("assignee", "Someone")}</strong>: {item.get("task", "")}</li>'
        else:
            html += '<li>No action items identified.</li>'
        
        html += """
                </ul>
            </div>
            
            <div class="participants">
                <h2>Participants</h2>
                <p>
        """
        
        # Add participants
        speakers = summary_data.get('speakers', [])
        if speakers:
            html += ', '.join(speakers)
        else:
            html += 'No participants identified.'
        
        html += """
                </p>
            </div>
            
            <div class="transcript">
                <h2>Full Transcript</h2>
                <pre>
        """
        
        # Add transcript
        transcript = summary_data.get('transcript', '')
        html += transcript.replace('<', '&lt;').replace('>', '&gt;')
        
        html += """
                </pre>
            </div>
        </body>
        </html>
        """
        
        return html
