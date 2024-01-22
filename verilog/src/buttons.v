// This is for the two buttons btn1 is 'input' btn2 is 'reset'

module buttons (
    input clk,
    input btn1,
    input btn2,
    output btn,
    output reset
);

parameter SIZE = 7;
// Use a counter to debounce the buttons
reg [SIZE:0] count;
reg reset_state;
reg btn_state;

initial begin
    count <= 0;
    reset_state <= 0;
    // btn <= 0;
    // reset <= 0;
end

always @(posedge clk) begin
    count <= count + 1'b1;
    
    // Debounce by reading state only on
    // count roll-over
    if (count == 0) begin
        // Button 1
        btn_state <= btn1;
        // Reset State
        reset_state <= btn2;
    end else begin
        // Reset set to 0 only pulses on counter
        reset_state <= 0; 
    end
end

assign reset = reset_state;
assign btn = btn_state;

endmodule