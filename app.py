import os
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import json
import tempfile
from fpdf import FPDF
from datetime import datetime

# Import LLM client handlers
from llm_clients import get_llm_client

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/error')
def error():
    """Render the error page."""
    error_message = request.args.get('message', 'An unknown error occurred')
    return render_template('error.html', error=error_message)

@app.route('/api/start_process', methods=['POST'])
def start_process():
    """Start the idea brainstorming process."""
    data = request.json
    keyword = data.get('keyword', '').strip()
    iterations = int(data.get('iterations', 3))
    
    if not keyword:
        return jsonify({'error': 'Please provide a keyword'}), 400
    
    if iterations < 2 or iterations > 5:
        return jsonify({'error': 'Iterations must be between 2 and 5'}), 400
    
    # Get LLM client
    try:
        llm_client = get_llm_client()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Initialize the conversation with the keyword
    conversation = []
    result_summary = {}
    
    try:
        # Initial brainstorming
        conversation.append({
            'role': 'system',
            'content': f'Starting brainstorming process for keyword: {keyword}'
        })
        
        # Start the iterative process
        current_idea = keyword
        
        for i in range(iterations):
            # LLM1: Brainstorm 3 ideas based on the current concept
            # Using a simpler prompt format that's more likely to succeed
            brainstorm_prompt = f"""Based on the concept: '{current_idea}', generate exactly 3 distinct, innovative ideas.

Keep it simple. For each idea, include only:
1. A title
2. A brief description
3. 2-3 key features

Format your response as a simple JSON structure like this:
{{
  "ideas": [
    {{
      "title": "First Idea Title",
      "description": "Brief description of first idea.",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Second Idea Title",
      "description": "Brief description of second idea.",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Third Idea Title",
      "description": "Brief description of third idea.",
      "key_features": ["Feature 1", "Feature 2"]
    }}
  ]
}}

Return ONLY this JSON structure without any additional text, explanations, or formatting.
"""
            
            # Try to generate brainstorm response with retry logic
            max_attempts = 3
            attempts = 0
            brainstorm_success = False
            brainstorm_response = None
            
            while attempts < max_attempts and not brainstorm_success:
                try:
                    app.logger.info(f"Attempt {attempts+1} to generate brainstorm ideas")
                    
                    # If this is the last attempt, use an even simpler fallback format
                    if attempts == max_attempts - 1:
                        simple_prompt = f"""Generate 3 simple ideas based on: '{current_idea}'.

Return ONLY a JSON object with this exact structure:
{{
  "ideas": [
    {{
      "title": "Idea 1",
      "description": "Description 1",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Idea 2",
      "description": "Description 2",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Idea 3",
      "description": "Description 3",
      "key_features": ["Feature 1", "Feature 2"]
    }}
  ]
}}

No commentary or explanations, just the JSON.
"""
                        brainstorm_response = llm_client.generate(simple_prompt, is_json=True, json_mode="strict")
                    else:
                        brainstorm_response = llm_client.generate(brainstorm_prompt, is_json=True, json_mode="strict")
                    
                    # Validate response structure
                    if 'ideas' not in brainstorm_response or not isinstance(brainstorm_response['ideas'], list) or len(brainstorm_response['ideas']) < 1:
                        raise ValueError("Response missing 'ideas' array or it's empty")
                    
                    # Ensure we have at least one idea
                    if len(brainstorm_response['ideas']) < 1:
                        # Create a default structure if necessary
                        brainstorm_response['ideas'] = [
                            {
                                "title": f"Idea based on {current_idea}",
                                "description": f"An innovative approach to {current_idea}.",
                                "key_features": ["Feature 1", "Feature 2", "Feature 3"]
                            }
                        ]
                    
                    # Ensure each idea has required fields
                    for idea in brainstorm_response['ideas']:
                        if 'title' not in idea:
                            idea['title'] = f"Idea related to {current_idea}"
                        if 'description' not in idea:
                            idea['description'] = f"A concept based on {current_idea}."
                        if 'key_features' not in idea or not isinstance(idea['key_features'], list):
                            idea['key_features'] = ["Innovative", "Practical", "User-friendly"]
                    
                    # Ensure we have exactly 3 ideas
                    while len(brainstorm_response['ideas']) < 3:
                        brainstorm_response['ideas'].append({
                            "title": f"Additional idea for {current_idea} #{len(brainstorm_response['ideas'])+1}",
                            "description": f"An alternative approach to {current_idea}.",
                            "key_features": ["Feature 1", "Feature 2", "Feature 3"]
                        })
                    
                    # If we have more than 3 ideas, keep only the first 3
                    if len(brainstorm_response['ideas']) > 3:
                        brainstorm_response['ideas'] = brainstorm_response['ideas'][:3]
                    
                    brainstorm_success = True
                except Exception as e:
                    attempts += 1
                    app.logger.error(f"Brainstorm attempt {attempts} failed: {str(e)}")
                    
                    if attempts >= max_attempts:
                        # Create a default response as a last resort
                        app.logger.warning(f"Using default brainstorm response after {max_attempts} failed attempts")
                        brainstorm_response = {
                            "ideas": [
                                {
                                    "title": f"Innovation in {current_idea} - Concept 1",
                                    "description": f"A novel approach to {current_idea} focusing on user experience and efficiency.",
                                    "key_features": ["User-friendly interface", "Efficient processing", "Scalable architecture"]
                                },
                                {
                                    "title": f"Enhanced {current_idea} Platform",
                                    "description": f"A comprehensive solution for {current_idea} with integrated analytics and automation.",
                                    "key_features": ["Integrated analytics", "Automated workflows", "Cloud-based solution"]
                                },
                                {
                                    "title": f"{current_idea} Reimagined",
                                    "description": f"A fresh perspective on {current_idea} targeting underserved market segments.",
                                    "key_features": ["Niche market focus", "Innovative business model", "Unique value proposition"]
                                }
                            ]
                        }
                        brainstorm_success = True
                    else:
                        # Try a different approach on the next attempt
                        brainstorm_prompt = f"""Generate 3 ideas about '{current_idea}'.

Output JSON with EXACTLY this structure:
{{
  "ideas": [
    {{
      "title": "Idea 1",
      "description": "Description 1",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Idea 2",
      "description": "Description 2",
      "key_features": ["Feature 1", "Feature 2"]
    }},
    {{
      "title": "Idea 3",
      "description": "Description 3",
      "key_features": ["Feature 1", "Feature 2"]
    }}
  ]
}}
"""
            
            # Add to conversation
            conversation.append({
                'role': 'assistant1',
                'content': brainstorm_response,
                'step': f'Iteration {i+1}: Brainstorming'
            })
            
            # LLM2: Evaluate the ideas - use a simpler format
            evaluate_prompt = f"""You are evaluating 3 ideas related to '{current_idea}'.

The ideas to evaluate are:
{json.dumps(brainstorm_response['ideas'], indent=2)}

For each idea, rate it from 1-10 on:
1. Solving a Real Problem
2. Market Potential
3. Feasibility for Individual Implementation

Add up the scores to get a total score for each idea.
Select the idea with the highest total score.

Respond with ONLY a JSON object using this exact structure:
{{
  "evaluations": [
    {{
      "title": "First Idea Title",
      "solving_real_problem": 8,
      "market_potential": 7,
      "feasibility": 9,
      "total_score": 24,
      "comments": "Brief comment on first idea"
    }},
    {{
      "title": "Second Idea Title",
      "solving_real_problem": 7,
      "market_potential": 8,
      "feasibility": 6,
      "total_score": 21,
      "comments": "Brief comment on second idea"
    }},
    {{
      "title": "Third Idea Title",
      "solving_real_problem": 9,
      "market_potential": 6,
      "feasibility": 8,
      "total_score": 23,
      "comments": "Brief comment on third idea"
    }}
  ],
  "selected_idea": {{
    "title": "First Idea Title",
    "description": "Description of the selected idea",
    "total_score": 24
  }}
}}
"""
            
            # Try to generate evaluation response with retry logic
            max_attempts = 3
            attempts = 0
            evaluation_success = False
            evaluation_response = None
            
            while attempts < max_attempts and not evaluation_success:
                try:
                    app.logger.info(f"Attempt {attempts+1} to generate evaluation")
                    
                    # If this is the last attempt, use an even simpler fallback format
                    if attempts == max_attempts - 1:
                        simple_prompt = f"""Evaluate these ideas:
{json.dumps(brainstorm_response['ideas'], indent=2)}

Return ONLY a JSON with:
{{
  "evaluations": [
    {{
      "title": "Idea 1 Title",
      "solving_real_problem": 8,
      "market_potential": 7,
      "feasibility": 9,
      "total_score": 24,
      "comments": "Comment"
    }},
    {{
      "title": "Idea 2 Title",
      "solving_real_problem": 7,
      "market_potential": 8,
      "feasibility": 6,
      "total_score": 21,
      "comments": "Comment"
    }},
    {{
      "title": "Idea 3 Title",
      "solving_real_problem": 9,
      "market_potential": 6,
      "feasibility": 8,
      "total_score": 23,
      "comments": "Comment"
    }}
  ],
  "selected_idea": {{
    "title": "Idea with highest score",
    "description": "Description",
    "total_score": 24
  }}
}}
"""
                        evaluation_response = llm_client.generate(simple_prompt, is_json=True, json_mode="strict")
                    else:
                        evaluation_response = llm_client.generate(evaluate_prompt, is_json=True, json_mode="strict")
                    
                    # Validate response structure
                    if 'evaluations' not in evaluation_response or not isinstance(evaluation_response['evaluations'], list):
                        raise ValueError("Response missing 'evaluations' array")
                    
                    if 'selected_idea' not in evaluation_response or not isinstance(evaluation_response['selected_idea'], dict):
                        raise ValueError("Response missing 'selected_idea' object")
                    
                    # Ensure we have evaluations for all ideas
                    if len(evaluation_response['evaluations']) < len(brainstorm_response['ideas']):
                        app.logger.warning("Evaluations array has fewer items than ideas array")
                        
                        # Generate default evaluations for missing ideas
                        idea_titles = [idea['title'] for idea in brainstorm_response['ideas']]
                        eval_titles = [eval['title'] for eval in evaluation_response['evaluations']]
                        
                        for title in idea_titles:
                            if title not in eval_titles:
                                evaluation_response['evaluations'].append({
                                    "title": title,
                                    "solving_real_problem": 7,
                                    "market_potential": 7,
                                    "feasibility": 7,
                                    "total_score": 21,
                                    "comments": f"Default evaluation for {title}"
                                })
                    
                    # Ensure each evaluation has required fields and the values are integers
                    for eval in evaluation_response['evaluations']:
                        for field in ['solving_real_problem', 'market_potential', 'feasibility']:
                            if field not in eval:
                                eval[field] = 7
                            else:
                                # Convert to integer if it's a string
                                try:
                                    eval[field] = int(eval[field])
                                except (ValueError, TypeError):
                                    eval[field] = 7
                        
                        if 'total_score' not in eval:
                            eval['total_score'] = eval['solving_real_problem'] + eval['market_potential'] + eval['feasibility']
                        else:
                            # Convert to integer if it's a string
                            try:
                                eval['total_score'] = int(eval['total_score'])
                            except (ValueError, TypeError):
                                eval['total_score'] = eval['solving_real_problem'] + eval['market_potential'] + eval['feasibility']
                        
                        if 'comments' not in eval:
                            eval['comments'] = f"Evaluation for {eval['title']}"
                    
                    # Ensure selected_idea has required fields
                    selected_idea = evaluation_response['selected_idea']
                    if 'title' not in selected_idea:
                        # Find the evaluation with the highest score
                        highest_score_eval = max(evaluation_response['evaluations'], key=lambda x: x['total_score'])
                        highest_score_idea = next((idea for idea in brainstorm_response['ideas'] if idea['title'] == highest_score_eval['title']), None)
                        
                        if highest_score_idea:
                            selected_idea['title'] = highest_score_idea['title']
                            if 'description' not in selected_idea:
                                selected_idea['description'] = highest_score_idea['description']
                            if 'total_score' not in selected_idea:
                                selected_idea['total_score'] = highest_score_eval['total_score']
                        else:
                            # Default if we can't find a match
                            selected_idea['title'] = brainstorm_response['ideas'][0]['title']
                            if 'description' not in selected_idea:
                                selected_idea['description'] = brainstorm_response['ideas'][0]['description']
                            if 'total_score' not in selected_idea:
                                selected_idea['total_score'] = 21
                    
                    evaluation_success = True
                except Exception as e:
                    attempts += 1
                    app.logger.error(f"Evaluation attempt {attempts} failed: {str(e)}")
                    
                    if attempts >= max_attempts:
                        # Create a default response as a last resort
                        app.logger.warning(f"Using default evaluation response after {max_attempts} failed attempts")
                        
                        # Find the first idea as our default selection
                        default_idea = brainstorm_response['ideas'][0]
                        
                        evaluation_response = {
                            "evaluations": [
                                {
                                    "title": brainstorm_response['ideas'][0]['title'],
                                    "solving_real_problem": 8,
                                    "market_potential": 7,
                                    "feasibility": 9,
                                    "total_score": 24,
                                    "comments": "This idea directly addresses user needs with a practical implementation path."
                                },
                                {
                                    "title": brainstorm_response['ideas'][1]['title'],
                                    "solving_real_problem": 7,
                                    "market_potential": 8,
                                    "feasibility": 6,
                                    "total_score": 21,
                                    "comments": "Has market potential but implementation may be challenging."
                                },
                                {
                                    "title": brainstorm_response['ideas'][2]['title'],
                                    "solving_real_problem": 9,
                                    "market_potential": 6,
                                    "feasibility": 8,
                                    "total_score": 23,
                                    "comments": "Excellent problem-solving but limited market reach."
                                }
                            ],
                            "selected_idea": {
                                "title": default_idea['title'],
                                "description": default_idea['description'],
                                "total_score": 24
                            }
                        }
                        evaluation_success = True
                    else:
                        # Try a different approach on the next attempt
                        evaluate_prompt = f"""Evaluate these 3 ideas:
{json.dumps(brainstorm_response['ideas'], indent=2)}

Rate each from 1-10 on: Problem-solving, Market potential, and Feasibility.

Return JSON with EXACTLY this structure:
{{
  "evaluations": [
    {{
      "title": "Idea 1 Title",
      "solving_real_problem": 8,
      "market_potential": 7,
      "feasibility": 9,
      "total_score": 24,
      "comments": "Comment"
    }},
    {{
      "title": "Idea 2 Title",
      "solving_real_problem": 7,
      "market_potential": 8,
      "feasibility": 6,
      "total_score": 21,
      "comments": "Comment"
    }},
    {{
      "title": "Idea 3 Title",
      "solving_real_problem": 9,
      "market_potential": 6,
      "feasibility": 8,
      "total_score": 23,
      "comments": "Comment"
    }}
  ],
  "selected_idea": {{
    "title": "Idea 1 Title",
    "description": "Description",
    "total_score": 24
  }}
}}
"""
            
            # Add to conversation
            conversation.append({
                'role': 'assistant2',
                'content': evaluation_response,
                'step': f'Iteration {i+1}: Evaluation'
            })
            
            # Update the current idea for the next iteration
            try:
                current_idea = evaluation_response['selected_idea']['title'] + ": " + evaluation_response['selected_idea']['description']
            except KeyError:
                # Fallback if we're missing fields
                current_idea = f"Refined idea based on {current_idea}"
            
            # If this is the last iteration, save the final idea
            if i == iterations - 1:
                try:
                    optimization_points = [
                        step['content']['selected_idea']['title'] 
                        for step in conversation 
                        if 'role' in step and step['role'] == 'assistant2' and 'content' in step and 'selected_idea' in step['content'] and 'title' in step['content']['selected_idea']
                    ]
                except (KeyError, TypeError):
                    # Fallback if we can't extract optimization points properly
                    optimization_points = [f"Iteration {j+1}" for j in range(iterations)]
                
                result_summary = {
                    'original_keyword': keyword,
                    'iterations_completed': iterations,
                    'final_idea': evaluation_response['selected_idea'],
                    'optimization_points': optimization_points
                }
    
    except Exception as e:
        app.logger.error(f"Error in idea process: {str(e)}")
        return jsonify({
            'error': f"An error occurred during the brainstorming process: {str(e)}. Please try again with a different keyword or check your API key settings."
        }), 500
    
    # Return the conversation and summary
    return jsonify({
        'conversation': conversation,
        'summary': result_summary
    })

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    """Generate a PDF report of the brainstorming process."""
    data = request.json
    conversation = data.get('conversation', [])
    summary = data.get('summary', {})
    
    if not conversation or not summary:
        return jsonify({'error': 'No data provided for PDF generation'}), 400
    
    try:
        # Create a PDF with support for basic encoding
        pdf = FPDF()
        pdf.add_page()
        
        # Helper function to sanitize text for PDF
        def sanitize_text(text):
            if not isinstance(text, str):
                text = str(text)
            # Replace problematic characters
            text = text.replace('\u2022', '*')  # Replace bullet points with asterisk for better alignment
            text = text.replace('\u2019', "'")  # Replace smart quotes
            text = text.replace('\u201C', '"')  # Replace smart quotes
            text = text.replace('\u201D', '"')  # Replace smart quotes
            text = text.replace('\u2013', '-')  # Replace en dash
            text = text.replace('\u2014', '--')  # Replace em dash
            # Remove any other non-Latin1 characters
            return ''.join(c for c in text if ord(c) < 256)
        
        # Set font
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=sanitize_text("Idea Forge - Brainstorming Report"), ln=True, align='C')
        pdf.ln(10)
        
        # Original keyword
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=sanitize_text(f"Original Concept: {summary.get('original_keyword', '')}"), ln=True)
        pdf.ln(5)
        
        # Final idea
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=sanitize_text("Final Idea:"), ln=True)
        pdf.set_font("Arial", size=12)
            
        final_idea = summary.get('final_idea', {})
        pdf.multi_cell(0, 10, txt=sanitize_text(f"Title: {final_idea.get('title', '')}"))
        pdf.multi_cell(0, 10, txt=sanitize_text(f"Description: {final_idea.get('description', '')}"))
        pdf.multi_cell(0, 10, txt=sanitize_text(f"Score: {final_idea.get('total_score', '')}"))
        pdf.ln(5)
        
        # Optimization points
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=sanitize_text("Development Path:"), ln=True)
        pdf.set_font("Arial", size=12)
            
        optimization_points = summary.get('optimization_points', [])
        for i, point in enumerate(optimization_points):
            pdf.multi_cell(0, 10, txt=sanitize_text(f"{i+1}. {point}"))
        
        pdf.ln(10)
        
        # Detailed conversation
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=sanitize_text("Detailed Process:"), ln=True)
        
        for entry in conversation:
            if 'role' not in entry or 'content' not in entry:
                continue
                
            role = entry.get('role', '')
            step = entry.get('step', '')
            
            if role == 'system':
                continue
                
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(0, 10, txt=sanitize_text(f"{step}"))
            pdf.set_font("Arial", size=10)
                
            if role == 'assistant1':
                # Brainstorming section
                pdf.set_font("Arial", 'I', 11)
                pdf.multi_cell(0, 10, txt=sanitize_text("Ideas Generated:"))
                
                ideas = entry.get('content', {}).get('ideas', [])
                for idea in ideas:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 10, txt=sanitize_text(f"* {idea.get('title', '')}"))
                    pdf.set_font("Arial", size=10)
                    
                    # Add some left margin for description for better alignment
                    pdf.set_x(pdf.get_x() + 5)
                    pdf.multi_cell(0, 10, txt=sanitize_text(f"{idea.get('description', '')}"))
                    
                    # Add key features with proper indentation if they exist
                    if 'key_features' in idea and isinstance(idea['key_features'], list) and idea['key_features']:
                        pdf.set_x(pdf.get_x() + 5)
                        pdf.multi_cell(0, 10, txt=sanitize_text("Key Features:"))
                        for feature in idea['key_features']:
                            pdf.set_x(pdf.get_x() + 10)
                            pdf.multi_cell(0, 10, txt=sanitize_text(f"* {feature}"))
                
            elif role == 'assistant2':
                # Evaluation section
                pdf.set_font("Arial", 'I', 11)
                pdf.multi_cell(0, 10, txt=sanitize_text("Evaluation:"))
                
                evaluations = entry.get('content', {}).get('evaluations', [])
                for eval in evaluations:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 10, txt=sanitize_text(f"* {eval.get('title', '')}"))
                    pdf.set_font("Arial", size=10)
                    
                    # Add some left margin for better alignment
                    pdf.set_x(pdf.get_x() + 5)
                    pdf.multi_cell(0, 10, txt=sanitize_text(f"Score: {eval.get('total_score', '')} ({eval.get('solving_real_problem', '')}/{eval.get('market_potential', '')}/{eval.get('feasibility', '')})"))
                    
                    pdf.set_x(pdf.get_x() + 5)
                    pdf.multi_cell(0, 10, txt=sanitize_text(f"Comments: {eval.get('comments', '')}"))
                
                # Selected idea
                selected = entry.get('content', {}).get('selected_idea', {})
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(0, 10, txt=sanitize_text(f"Selected Idea: {selected.get('title', '')}"))
                
            pdf.ln(5)
        
        # Add timestamp
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, txt=sanitize_text(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"), ln=True, align='R')
        
        # Save the PDF to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
            
        pdf.output(pdf_path)
        
        # Return the file for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"idea_forge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f"Failed to generate PDF: {str(e)}"}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Server error occurred"), 500

if __name__ == '__main__':
    app.run(debug=True) 