import json
import re
from typing import Dict, Any, Optional

def parse_twitch_message(raw_message: str) -> Optional[Dict[str, Any]]:
    """
    Parse a Twitch IRC message into a structured JSON object.
    
    Args:
        raw_message: Raw IRC message string from Twitch
        
    Returns:
        Dictionary containing parsed message data, or None if parsing fails
    """
    if not raw_message or not raw_message.strip():
        return None
    
    # Remove trailing whitespace and newlines
    message = raw_message.strip()
    
    # Initialize result dictionary
    result = {
        "tags": {},
        "source": {},
        "command": "",
        "parameters": [],
        "channel": "",
        "message": ""
    }
    
    # Parse tags (if present)
    if message.startswith('@'):
        # Find the end of tags section
        tags_end = message.find(' ')
        if tags_end == -1:
            return None
            
        tags_section = message[1:tags_end]  # Remove @ prefix
        message = message[tags_end + 1:]    # Remove tags from message
        
        # Parse individual tags
        for tag in tags_section.split(';'):
            if '=' in tag:
                key, value = tag.split('=', 1)
                # Handle special cases for certain tags
                if key == 'badges' and value:
                    # Parse badges into a list of objects
                    badges = []
                    for badge in value.split(','):
                        if '/' in badge:
                            badge_name, badge_version = badge.split('/', 1)
                            badges.append({"name": badge_name, "version": badge_version})
                    result["tags"][key] = badges
                elif key == 'emotes' and value:
                    # Parse emotes (format: emote_id:start-end,start-end/emote_id:start-end)
                    emotes = []
                    for emote_group in value.split('/'):
                        if ':' in emote_group:
                            emote_id, positions = emote_group.split(':', 1)
                            emote_positions = []
                            for pos in positions.split(','):
                                if '-' in pos:
                                    start, end = pos.split('-')
                                    emote_positions.append({"start": int(start), "end": int(end)})
                            emotes.append({"id": emote_id, "positions": emote_positions})
                    result["tags"][key] = emotes
                elif key in ['mod', 'subscriber', 'turbo', 'first-msg', 'returning-chatter']:
                    # Convert boolean-like tags
                    result["tags"][key] = value == '1'
                elif key in ['room-id', 'user-id', 'tmi-sent-ts']:
                    # Convert numeric tags
                    result["tags"][key] = int(value) if value else None
                else:
                    # Store as string, empty values as None
                    result["tags"][key] = value if value else None
    
    # Parse source (prefix)
    if message.startswith(':'):
        # Find the end of source section
        source_end = message.find(' ')
        if source_end == -1:
            return None
            
        source_section = message[1:source_end]  # Remove : prefix
        message = message[source_end + 1:]      # Remove source from message
        
        # Parse source components
        if '!' in source_section:
            # Format: nick!user@host
            nick_part, host_part = source_section.split('!', 1)
            result["source"]["nick"] = nick_part
            
            if '@' in host_part:
                user, host = host_part.split('@', 1)
                result["source"]["user"] = user
                result["source"]["host"] = host
            else:
                result["source"]["user"] = host_part
        else:
            # Just a hostname
            result["source"]["host"] = source_section
    
    # Parse command and parameters
    parts = message.split(' ')
    if parts:
        result["command"] = parts[0]
        
        # Handle PRIVMSG specifically
        if result["command"] == "PRIVMSG" and len(parts) >= 3:
            result["channel"] = parts[1]
            # Message content starts after the channel and ':'
            message_start = message.find(':', len(parts[0]) + len(parts[1]) + 2)
            if message_start != -1:
                result["message"] = message[message_start + 1:]
            
            result["parameters"] = parts[1:]
        else:
            result["parameters"] = parts[1:]
    
    return result

def extract_mentions(message: str) -> list[str]:
    """
    Extract all mentions from a Twitch chat message.
    
    Args:
        message: The message content string
        
    Returns:
        List of mentioned usernames (without the @ symbol)
    """
    if not message:
        return []
    
    # Find all @mentions using regex
    # This pattern matches @ followed by alphanumeric characters and underscores
    mention_pattern = r'@([a-zA-Z0-9_]+)'
    mentions = re.findall(mention_pattern, message)
    
    return mentions

def check_if_mentioned(message: str, username: str) -> bool:
    """
    Check if a specific user is mentioned in the message.
    
    Args:
        message: The message content string
        username: Username to check for (case insensitive)
        
    Returns:
        True if the user is mentioned, False otherwise
    """
    mentions = extract_mentions(message)
    return username.lower() in [mention.lower() for mention in mentions]

def format_message_json(parsed_message: Dict[str, Any], indent: int = 2) -> str:
    """
    Format the parsed message as a pretty JSON string.
    
    Args:
        parsed_message: Dictionary from parse_twitch_message
        indent: JSON indentation level
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(parsed_message, indent=indent, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    # Test with the provided message
    test_message = "@badge-info=;badges=moderator/1,gone-bananas/1;client-nonce=988ef465af244773f3aa3dedc5d860fe;color=#D2691E;display-name=JRCosta;emotes=;first-msg=0;flags=;id=a5c0992a-e7ba-4f8a-8de7-afec4c82c0ed;mod=1;returning-chatter=0;room-id=462756951;subscriber=0;tmi-sent-ts=1749523228929;turbo=0;user-id=128682316;user-type=mod :jrcosta!jrcosta@jrcosta.tmi.twitch.tv PRIVMSG #el_pipow :yo"
    
    # Test message with mentions
    test_message_with_mention = "@badge-info=;badges=moderator/1,gone-bananas/1;client-nonce=dd5258fb0b33868f567563e298c079d9;color=#D2691E;display-name=JRCosta;emotes=;first-msg=0;flags=;id=f2389d9a-7a62-40b6-926d-0916edff407d;mod=1;returning-chatter=0;room-id=462756951;subscriber=0;tmi-sent-ts=1749523513526;turbo=0;user-id=128682316;user-type=mod :jrcosta!jrcosta@jrcosta.tmi.twitch.tv PRIVMSG #el_pipow :@El_Pipow yo"
    
    parsed = parse_twitch_message(test_message)
    if parsed:
        print("Message without mentions:")
        print(format_message_json(parsed))
        print(f"Mentions found: {extract_mentions(parsed['message'])}")
        print(f"Is El_Pipow mentioned? {check_if_mentioned(parsed['message'], 'El_Pipow')}")
        print()
    
    parsed_with_mention = parse_twitch_message(test_message_with_mention)
    if parsed_with_mention:
        print("Message with mentions:")
        print(format_message_json(parsed_with_mention))
        print(f"Mentions found: {extract_mentions(parsed_with_mention['message'])}")
        print(f"Is El_Pipow mentioned? {check_if_mentioned(parsed_with_mention['message'], 'El_Pipow')}") 