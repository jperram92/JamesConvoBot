"""
LangChain agent for AI Meeting Assistant.
"""
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain.callbacks.manager import CallbackManager
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage

from agent_core.llm_manager import OpenAILLM
from agent_core.memory import MeetingMemory
from tools.data_query import DataQueryTool
from tools.email_sender import EmailSenderTool
from tools.web_search import WebSearchTool
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class MeetingAgent:
    """LangChain agent for AI Meeting Assistant."""
    
    def __init__(self, meeting_id: str):
        """
        Initialize the meeting agent.
        
        Args:
            meeting_id: ID of the meeting.
        """
        self.meeting_id = meeting_id
        self.name = config.get('agent.name', 'Augment')
        self.trigger_word = config.get('agent.trigger_word', 'Augment')
        self.response_threshold = config.get('agent.response_threshold', 0.7)
        
        # Initialize memory
        self.memory = MeetingMemory(meeting_id)
        
        # Initialize LLM
        self.llm = OpenAILLM(
            model_name=config.get('llm.model', 'gpt-4'),
            temperature=config.get('llm.temperature', 0.7),
            max_tokens=config.get('llm.max_tokens', 1000)
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent = self._initialize_agent()
        
        logger.info(f"Initialized meeting agent for meeting {meeting_id}")
    
    def _initialize_tools(self) -> List[Any]:
        """
        Initialize tools for the agent.
        
        Returns:
            List of tools.
        """
        tools = []
        
        # Add web search tool if enabled
        if config.get('agent.tools.web_search', True):
            tools.append(WebSearchTool())
        
        # Add email tool if enabled
        if config.get('agent.tools.email', True):
            tools.append(EmailSenderTool())
        
        # Add data query tool if enabled
        if config.get('agent.tools.data_query', True):
            tools.append(DataQueryTool())
        
        return tools
    
    def _initialize_agent(self) -> AgentExecutor:
        """
        Initialize the LangChain agent.
        
        Returns:
            AgentExecutor instance.
        """
        # Create system message
        system_message = SystemMessage(
            content=config.get(
                'llm.system_prompt',
                f"You are {self.name}, an AI meeting assistant. "
                f"You help with meeting transcription, answering questions, and providing summaries. "
                f"You can search the web, send emails, and query company data to provide helpful information. "
                f"Always be concise, professional, and helpful."
            )
        )
        
        # Create agent prompt
        prompt = [
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
        
        # Create agent
        agent = OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory.agent_memory,
            verbose=True
        )
    
    def process_transcript(self, speaker: str, text: str) -> Optional[str]:
        """
        Process a transcript entry and generate a response if needed.
        
        Args:
            speaker: Name or ID of the speaker.
            text: Transcribed text.
            
        Returns:
            Response from the agent, or None if no response is needed.
        """
        # Add entry to transcript
        self.memory.add_transcript_entry(speaker, text)
        
        # Check if the trigger word is in the text
        if self.trigger_word.lower() in text.lower():
            # Extract the query (text after the trigger word)
            query = text[text.lower().find(self.trigger_word.lower()) + len(self.trigger_word):].strip()
            
            # If there's no query, don't respond
            if not query:
                return None
            
            # Generate response
            try:
                response = self.agent.run(query)
                
                # Add response to transcript
                self.memory.add_transcript_entry(self.name, response, is_assistant=True)
                
                return response
            
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                error_response = f"I'm sorry, I encountered an error: {str(e)}"
                
                # Add error response to transcript
                self.memory.add_transcript_entry(self.name, error_response, is_assistant=True)
                
                return error_response
        
        return None
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the meeting.
        
        Returns:
            Dictionary containing the summary and action items.
        """
        # Get the full transcript
        transcript_text = self.memory.get_transcript_text()
        
        # Create prompt for summary generation
        prompt = (
            f"Please summarize the following meeting transcript and extract action items. "
            f"Format the summary in a clear, professional way. "
            f"Include key points discussed, decisions made, and action items with assignees if mentioned.\n\n"
            f"Transcript:\n{transcript_text}"
        )
        
        try:
            # Generate summary
            summary_response = self.llm._call(prompt)
            
            # Parse summary and action items
            # For simplicity, we'll just return the full response
            # In a real implementation, you might want to parse this into structured data
            return {
                "summary": summary_response,
                "action_items": [],  # Would be parsed from the response
                "transcript": transcript_text
            }
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "action_items": [],
                "transcript": transcript_text
            }
    
    def send_summary_email(self, recipients: List[str]) -> str:
        """
        Generate and send a summary email.
        
        Args:
            recipients: List of email recipients.
            
        Returns:
            Status message.
        """
        # Generate summary
        summary_data = self.generate_summary()
        
        # Create email subject
        subject = f"Meeting Summary: {self.meeting_id}"
        
        # Create email body
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; }}
                .summary {{ margin-bottom: 20px; }}
                .action-items {{ margin-bottom: 20px; }}
                .action-item {{ margin-bottom: 10px; }}
                .transcript {{ font-size: 0.9em; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <h1>Meeting Summary: {self.meeting_id}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>{summary_data['summary']}</p>
            </div>
            
            <div class="action-items">
                <h2>Action Items</h2>
                <ul>
        """
        
        # Add action items
        if summary_data['action_items']:
            for item in summary_data['action_items']:
                body += f'<li class="action-item">{item}</li>'
        else:
            body += '<li>No action items identified.</li>'
        
        body += """
                </ul>
            </div>
            
            <div class="transcript">
                <h2>Full Transcript</h2>
                <pre>{}</pre>
            </div>
        </body>
        </html>
        """.format(summary_data['transcript'].replace('<', '&lt;').replace('>', '&gt;'))
        
        # Find email tool
        email_tool = None
        for tool in self.tools:
            if tool.name == "email_sender":
                email_tool = tool
                break
        
        if email_tool:
            # Send email
            return email_tool._run(recipients, subject, body)
        else:
            return "Email tool not available."
