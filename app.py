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
    llm_client = get_llm_client()
    
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
            brainstorm_prompt = f"""Based on the concept: '{current_idea}', brainstorm 3 distinct, innovative ideas.
            For each idea, provide:
            1. A concise title
            2. A brief description (2-3 sentences)
            3. Key features or aspects
            
            Format your response as a JSON object with the structure:
            {{
                "ideas": [
                    {{
                        "title": "Idea 1 Title",
                        "description": "Description of idea 1",
                        "key_features": ["Feature 1", "Feature 2", "Feature 3"]
                    }},
                    ...
                ]
            }}
            """
            
            brainstorm_response = llm_client.generate(brainstorm_prompt, is_json=True)
            
            # Add to conversation
            conversation.append({
                'role': 'assistant1',
                'content': brainstorm_response,
                'step': f'Iteration {i+1}: Brainstorming'
            })
            
            # LLM2: Evaluate the ideas
            evaluate_prompt = f"""Evaluate the following 3 ideas based on these criteria:
            1. Solving a Real Problem (1-10)
            2. Market Potential (1-10)
            3. Feasibility for Individual Implementation (1-10)
            
            Ideas to evaluate:
            {json.dumps(brainstorm_response['ideas'])}
            
            Calculate a total score for each idea (sum of all criteria).
            Select the idea with the highest total score.
            
            Format your response as a JSON object with the structure:
            {{
                "evaluations": [
                    {{
                        "title": "Idea 1 Title",
                        "solving_real_problem": 8,
                        "market_potential": 7,
                        "feasibility": 9,
                        "total_score": 24,
                        "comments": "Brief evaluation comments"
                    }},
                    ...
                ],
                "selected_idea": {{
                    "title": "Selected Idea Title",
                    "description": "Description of the selected idea",
                    "total_score": 24
                }}
            }}
            """
            
            evaluation_response = llm_client.generate(evaluate_prompt, is_json=True)
            
            # Add to conversation
            conversation.append({
                'role': 'assistant2',
                'content': evaluation_response,
                'step': f'Iteration {i+1}: Evaluation'
            })
            
            # Update the current idea for the next iteration
            current_idea = evaluation_response['selected_idea']['title'] + ": " + evaluation_response['selected_idea']['description']
            
            # If this is the last iteration, save the final idea
            if i == iterations - 1:
                result_summary = {
                    'original_keyword': keyword,
                    'iterations_completed': iterations,
                    'final_idea': evaluation_response['selected_idea'],
                    'optimization_points': [step['content']['selected_idea']['title'] for step in conversation if 'role' in step and step['role'] == 'assistant2']
                }
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Idea Forge - Brainstorming Report", ln=True, align='C')
        pdf.ln(10)
        
        # Original keyword
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Original Concept: {summary.get('original_keyword', '')}", ln=True)
        pdf.ln(5)
        
        # Final idea
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Final Idea:", ln=True)
        pdf.set_font("Arial", size=12)
        
        final_idea = summary.get('final_idea', {})
        pdf.multi_cell(0, 10, txt=f"Title: {final_idea.get('title', '')}")
        pdf.multi_cell(0, 10, txt=f"Description: {final_idea.get('description', '')}")
        pdf.multi_cell(0, 10, txt=f"Score: {final_idea.get('total_score', '')}")
        pdf.ln(5)
        
        # Optimization points
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Development Path:", ln=True)
        pdf.set_font("Arial", size=12)
        
        optimization_points = summary.get('optimization_points', [])
        for i, point in enumerate(optimization_points):
            pdf.multi_cell(0, 10, txt=f"{i+1}. {point}")
        
        pdf.ln(10)
        
        # Detailed conversation
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Detailed Process:", ln=True)
        
        for entry in conversation:
            if 'role' not in entry or 'content' not in entry:
                continue
                
            role = entry.get('role', '')
            step = entry.get('step', '')
            
            if role == 'system':
                continue
                
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(0, 10, txt=f"{step}")
            pdf.set_font("Arial", size=10)
            
            if role == 'assistant1':
                # Brainstorming section
                pdf.set_font("Arial", 'I', 11)
                pdf.multi_cell(0, 10, txt="Ideas Generated:")
                
                ideas = entry.get('content', {}).get('ideas', [])
                for idea in ideas:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 10, txt=f"• {idea.get('title', '')}")
                    pdf.set_font("Arial", size=10)
                    pdf.multi_cell(0, 10, txt=f"  {idea.get('description', '')}")
                    
            elif role == 'assistant2':
                # Evaluation section
                pdf.set_font("Arial", 'I', 11)
                pdf.multi_cell(0, 10, txt="Evaluation:")
                
                evaluations = entry.get('content', {}).get('evaluations', [])
                for eval in evaluations:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 10, txt=f"• {eval.get('title', '')}")
                    pdf.set_font("Arial", size=10)
                    pdf.multi_cell(0, 10, txt=f"  Score: {eval.get('total_score', '')} ({eval.get('solving_real_problem', '')}/{eval.get('market_potential', '')}/{eval.get('feasibility', '')})")
                    pdf.multi_cell(0, 10, txt=f"  Comments: {eval.get('comments', '')}")
                
                # Selected idea
                selected = entry.get('content', {}).get('selected_idea', {})
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(0, 10, txt=f"Selected Idea: {selected.get('title', '')}")
                
            pdf.ln(5)
        
        # Add timestamp
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='R')
        
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 